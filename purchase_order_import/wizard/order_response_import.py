# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.tools import config, float_compare
from odoo.exceptions import UserError, ValidationError
import logging
import mimetypes
from lxml import etree

logger = logging.getLogger(__name__)

ORDER_RESPONSE_STATUS_ACK = "acknowledgement"
ORDER_RESPONSE_STATUS_ACCEPTED = "accepted"
ORDER_RESPONSE_STATUS_REJECTED = "rejected"
ORDER_RESPONSE_STATUS_CONDITIONAL = "conditionally_accepted"

LINE_STATUS_ACCEPTED = "accepted"
LINE_STATUS_REJECTED = "rejected"
LINE_STATUS_AMEND = "amend"


def is_int(val):
    try:
        int(val)
        return True
    except ValueError:
        return False


class OrderResponseImport(models.TransientModel):
    _name = "order.response.import"
    _description = "Purchase Order Response Import from Files"

    @api.model
    def _get_purchase_id(self):
        assert (
            self._context["active_model"] == "purchase.order"
        ), "bad active_model"
        return self.env["purchase.order"].browse(self._context["active_id"])

    document = fields.Binary(
        string="XML or PDF Order response",
        required=True,
        help="Upload an Order response file that you received from "
        "your supplier. Supported formats: XML and PDF "
        "(PDF with an embeded XML file).",
    )
    filename = fields.Char(string="Filename")

    @api.model
    def parse_xml_order_document(self, xml_root):
        raise UserError(
            _(
                "This type of XML Order Response is not supported. Did you "
                "install the module to support this XML format?"
            )
        )

    @api.model
    def parse_pdf_order_document(self, document):
        """
        Get PDF attachments, filter on XML files and call import_order_xml
        """
        xml_files_dict = self.get_xml_files_from_pdf(document)
        if not xml_files_dict:
            raise UserError(
                _("There are no embedded XML file in this PDF file.")
            )
        for xml_filename, xml_root in xml_files_dict.iteritems():
            logger.info("Trying to parse XML file %s", xml_filename)
            try:
                parsed_order_document = self.parse_xml_order_document(xml_root)
                return parsed_order_document
            except:
                continue
        raise UserError(
            _(
                "This type of XML Order Document is not supported. Did you "
                "install the module to support this XML format?"
            )
        )

    # Format of parsed order response
    # {
    # 'ref': 'SO01234' # the buyer party identifier
    #                  # (specified into the Order document -> po's name)
    # 'supplier': {'vat': 'FR25499247138'},
    # 'company': {'vat': 'FR12123456789'}, # Only used to check we are not
    #                                      # importing the quote in the
    #                                      # wrong company by mistake
    # 'status': 'acknowledgement | accepted | rejected |
    #            conditionally_accepted'
    # 'currency': {'iso': 'EUR', 'symbol': u'€'},
    # 'note': 'some notes',
    # 'chatter_msg': ['msg1', 'msg2']
    # 'lines': [{
    #           'id': 123456,
    #           'qty': 2.5,
    #           'uom': {'unece_code': 'C62'},
    #           'status': 5,
    #           'note': 'my note'
    #           'backorder_qty: None  # if provided and qty != expected
    #                                 # the backorder qty will be delivered
    #                                 # in a next shipping
    #    }]

    @api.model
    def parse_order_response(self, document, filename):
        if not document:
            raise UserError(_("Missing document file"))
        if not filename:
            raise UserError(_("Missing document filename"))
        filetype = mimetypes.guess_type(filename)[0]
        logger.debug("OrderResponse file mimetype: %s", filetype)
        if filetype in ["application/xml", "text/xml"]:
            try:
                xml_root = etree.fromstring(document)
            except:
                logger.exception("File is not XML-compliant")
                raise UserError(_("This XML file is not XML-compliant"))
            if logger.isEnabledFor(logging.DEBUG):
                pretty_xml_string = etree.tostring(
                    xml_root,
                    pretty_print=True,
                    encoding="UTF-8",
                    xml_declaration=True,
                )
                logger.debug("Starting to import the following XML file:")
                logger.debug(pretty_xml_string)
            parsed_order_document = self.parse_xml_order_document(xml_root)
        elif filetype == "application/pdf":
            parsed_order_document = self.parse_pdf_order_document(document)
        else:
            raise UserError(
                _(
                    "This file '%s' is not recognised as XML nor PDF file. "
                    "Please check the file and it's extension."
                )
                % filename
            )
        logger.debug(
            "Result of OrderResponse parsing: ", parsed_order_document
        )
        if "attachments" not in parsed_order_document:
            parsed_order_document["attachments"] = {}
        parsed_order_document["attachments"][filename] = document.encode(
            "base64"
        )
        if "chatter_msg" not in parsed_order_document:
            parsed_order_document["chatter_msg"] = []
        if (
            parsed_order_document.get("company")
            and not config["test_enable"]
            and not self._context.get("edi_skip_company_check")
        ):
            self.env["business.document.import"]._check_company(
                parsed_order_document["company"],
                parsed_order_document["chatter_msg"],
            )
        return parsed_order_document

    @api.multi
    def process_document(self):
        self.ensure_one()
        parsed_order_document = self.parse_order_response(
            self.document.decode("base64"), self.filename
        )
        self.process_data(parsed_order_document)

    @api.model
    def process_data(self, parsed_order_document):
        bdio = self.env["business.document.import"]
        po_name = parsed_order_document.get("ref")
        order = self.env["purchase.order"].search([("name", "=", po_name)])
        if not order:
            self.env["business.document.import"].user_error_wrap(
                _("No purchase order found for name %s.") % po_name
            )

        currency = bdio._match_currency(
            parsed_order_document.get("currency"),
            parsed_order_document["chatter_msg"],
        )
        partner = bdio._match_partner(
            parsed_order_document["supplier"],
            parsed_order_document["chatter_msg"],
            partner_type="supplier",
        )
        if (
            partner.commercial_partner_id
            != order.partner_id.commercial_partner_id
        ):
            bdio.user_error_wrap(
                _(
                    "The supplier of the imported OrderResponse (%s) "
                    "is different from the supplier of the purchase order "
                    "(%s)."
                    % (
                        partner.commercial_partner_id.name,
                        order.partner_id.commercial_partner_id.name,
                    )
                )
            )
        if currency and currency != order.currency_id:
            bdio.user_error_wrap(
                _(
                    "The currency of the imported OrderResponse (%s) "
                    "is different from the currency of the purchase order "
                    "(%s)."
                )
                % (currency.name, order.currency_id.name)
            )

        status = parsed_order_document.get("status")
        if status == ORDER_RESPONSE_STATUS_ACK:
            self._process_ack(order, parsed_order_document)
        elif status == ORDER_RESPONSE_STATUS_REJECTED:
            self._process_rejected(order, parsed_order_document)
        elif status == ORDER_RESPONSE_STATUS_ACCEPTED:
            self._process_accepted(order, parsed_order_document)
        elif status == ORDER_RESPONSE_STATUS_CONDITIONAL:
            self._process_conditional(order, parsed_order_document)
        else:
            bdio.user_error_wrap(_("Unknown status '%s'.") % status)

        bdio.post_create_or_update(parsed_order_document, order)
        logger.info(
            "purchase.order ID %d updated via import of file %s.",
            order.id,
            self.filename,
        )
        order.message_post(
            _(
                "This purchase order has been updated automatically"
                " via the import of OrderResponse file %s."
            )
            % self.filename
        )
        return order.get_formview_action()

    @api.model
    def _process_ack(self, purchase_order, parsed_order_document):
        if not purchase_order.supplier_ack_dt:
            purchase_order.supplier_ack_dt = fields.Datetime.now()

    @api.model
    def _process_rejected(self, purchase_order, parsed_order_document):
        parsed_order_document["chatter_msg"] = (
            parsed_order_document["chatter_msg"] or []
        )
        parsed_order_document["chatter_msg"].append(
            _("PO cancelled by the supplier.")
        )
        purchase_order.button_cancel()

    @api.model
    def _process_accepted(self, purchase_order, parsed_order_document):
        parsed_order_document["chatter_msg"] = (
            parsed_order_document["chatter_msg"] or []
        )
        parsed_order_document["chatter_msg"].append(
            _("PO confirmed by the supplier.")
        )
        purchase_order.button_approve()

    @api.model
    def _process_conditional(self, purchase_order, parsed_order_document):
        chatter = parsed_order_document["chatter_msg"] = (
            parsed_order_document["chatter_msg"] or []
        )
        chatter.append(_("PO confirmed with amendment by the supplier."))
        lines = parsed_order_document["lines"]
        line_ids = [int(l["line_id"]) for l in lines if is_int(l["line_id"])]
        if set(line_ids) != set(purchase_order.order_line.ids):
            self.env["business.document.import"].user_error_wrap(
                _(
                    "Unable to conditionally confirm the purchase order. \n"
                    "Line IDS into the parsed document differs from the "
                    "expected list of order line ids: \n "
                    "received: %s\n"
                    "expected: %s\n"
                )
                % (
                    [l["line_id"] for l in lines],
                    purchase_order.order_line.ids,
                )
            )
            return
        purchase_order.button_approve()
        # apply changes to the created moves...
        lines_by_id = {int(l["line_id"]): l for l in lines}
        for order_line in purchase_order.order_line:
            line_info = lines_by_id[order_line.id]
            note = line_info.get("note")
            moves = order_line.move_ids.filtered(
                lambda x: x.state not in ("cancel", "done")
            )
            if not moves:
                self.env["business.document.import"].user_error_wrap(
                    _("No move found for PO line.\n" "Line Info: %s")
                    % line_info
                )
            if note:
                moves.write({"note": note})
            status = line_info["status"]
            if status == LINE_STATUS_ACCEPTED:
                self._process_line_accepted(line_info, order_line, moves)
            elif status == LINE_STATUS_REJECTED:
                self._process_line_rejected(line_info, order_line, moves)
            elif status == LINE_STATUS_AMEND:
                self._process_line_amended(line_info, order_line, moves)

    def _process_line_accepted(self, line_info, order_line, moves):
        pass

    def _process_line_rejected(self, line_info, order_line, moves):
        moves.action_cancel()

    def _process_line_amended(self, line_info, order_line, moves):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        qty = line_info["qty"]
        backorder_qty = line_info["backorder_qty"]
        moves_qty = sum(moves.mapped("product_qty"))
        if float_compare(qty, moves_qty, precision_digits=precision) >= 0:
            return

        # confirmed qty < ordered qty
        move_ids_to_backorder = []
        move_ids_to_cancel = []
        for move in moves:
            self._check_picking_status(move.picking_id)
            if (
                float_compare(
                    qty, move.product_qty, precision_digits=precision
                )
                >= 0
            ):
                # qty planned => qty into the stock move: Keep it
                qty -= move.product_qty
                continue
            if (
                qty
                and float_compare(
                    qty, move.product_qty, precision_digits=precision
                )
                < 0
            ):
                # qty planned < qty into the stock move: Split it
                new_move_id = move.split(move.product_qty - qty)
                move = self.env["stock.move"].browse(new_move_id)
            qty -= move.product_qty
            if not backorder_qty:
                # if no backorder -> we must cancel the move
                move_ids_to_cancel.append(move.id)
                continue
            # from here we process the backorder qty
            # we distribute this qty into the remaining moves and
            # if this qty is < than the expected one, we split and cancel the
            # remaining qty
            if (
                float_compare(
                    backorder_qty, move.product_qty, precision_digits=precision
                )
                < 0
            ):
                # backorder_qty < qty into the move -> split the move
                # anf cancel remaining qty
                move_ids_to_cancel.append(
                    move.split(move.product_qty - backorder_qty)
                )
            if move.split_from:
                # Add not on the original move to say that items will be
                # delivered into a next delivery
                note = line_info.get("note")
                note = note + "\n" if note else ""
                note += (
                    _("%s items should be delivered into a next delivery.")
                    % move.product_qty
                )
                move.split_from.note = note
            backorder_qty -= move.product_qty
            move_ids_to_backorder.append(move.id)
        # move backorder moves to a backorder
        if move_ids_to_backorder:
            moves_to_backorder = self.env["stock.move"].browse(
                move_ids_to_backorder
            )
            self._add_moves_to_backorder(moves_to_backorder)
        # cancel moves to cancel
        if move_ids_to_cancel:
            moves_to_cancel = self.env["stock.move"].browse(move_ids_to_cancel)
            moves_to_cancel.action_cancel()
            moves_to_cancel.write(
                {"note": _("No backorder planned by the supplier.")}
            )
        # Reset Operations
        moves[0].picking_id.do_prepare_partial()

    @api.model
    def _add_moves_to_backorder(self, moves):
        """
        Add the moves to the picking's backorder
        return the backorder associated to the current picking. If no backorder
        exists, create a new one.
        :param moves:
        """
        StockPicking = self.env["stock.picking"]
        current_picking = moves[0].picking_id
        backorder = StockPicking.search(
            [("backorder_id", "=", current_picking.id)]
        )
        if not backorder:
            date_done = current_picking.date_done
            current_picking._create_backorder(backorder_moves=moves)
            # preserve date_done....
            current_picking.date_done = date_done
        else:
            moves.write({"picking_id": backorder.id})
            backorder.action_confirm()
            backorder.action_assign()

    @api.model
    def _check_picking_status(self, picking):
        """
        The picking operations have already begun
        :param picking:
        :return:
        """
        if any(
            operation.qty_done != 0 for operation in picking.pack_operation_ids
        ):
            raise ValidationError(
                _(
                    "Some Pack Operations have already started! "
                    "Please validate or reset operations on "
                    "picking %s to ensure delivery slip to be computed."
                )
                % picking.name
            )
