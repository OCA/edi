# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import mimetypes
from base64 import b64decode, b64encode

from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import config, float_compare

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


class PurchaseOrderResponseImport(models.TransientModel):
    _name = "purchase.order.response.import"
    _description = "Purchase Order Response Import from Files"

    document = fields.Binary(
        string="XML or PDF Order response",
        required=True,
        help="Upload an Order response file that you received from "
        "your supplier. Supported formats: XML and PDF "
        "(PDF with an embeded XML file).",
    )
    filename = fields.Char()

    @api.model
    def parse_xml_order_document(self, xml_root):
        raise UserError(
            self.env._(
                "This type of XML Order Response is not supported. Did you "
                "install the module to support this XML format?"
            )
        )

    @api.model
    def parse_pdf_order_document(self, document):
        """
        Get PDF attachments, filter on XML files and call import_order_xml
        """
        xml_files_dict = self.env["pdf.xml.tool"].pdf_get_xml_files(document)
        if not xml_files_dict:
            raise UserError(
                self.env._("There are no embedded XML file in this PDF file.")
            )
        for xml_filename, xml_root in xml_files_dict.items():
            logger.info("Trying to parse XML file %s", xml_filename)
            try:
                parsed_order_document = self.parse_xml_order_document(xml_root)
                return parsed_order_document
            except:  # noqa: E722
                continue
        raise UserError(
            self.env._(
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
            raise UserError(self.env._("Missing document file"))
        if not filename:
            raise UserError(self.env._("Missing document filename"))
        filetype = mimetypes.guess_type(filename)[0]
        logger.debug("OrderResponse file mimetype: %s", filetype)
        if filetype in ["application/xml", "text/xml"]:
            try:
                xml_root = etree.fromstring(document)
            except etree.XMLSyntaxError as e:
                logger.exception("File is not XML-compliant")
                raise UserError(self.env._("This XML file is not XML-compliant")) from e
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
                self.env._(
                    "This file '%(filename)s' is not recognised as XML nor PDF file. "
                    "Please check the file and it's extension.",
                    filename=filename,
                )
            )
        logger.debug("Result of OrderResponse parsing: ", parsed_order_document)
        if "attachments" not in parsed_order_document:
            parsed_order_document["attachments"] = {}
        parsed_order_document["attachments"][filename] = b64encode(document).decode()
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

    def process_document(self):
        self.ensure_one()
        parsed_order_document = self.parse_order_response(
            b64decode(self.document), self.filename
        )
        self.process_data(parsed_order_document)

    @api.model
    def process_data(self, parsed_order_document):
        bdio = self.env["business.document.import"]
        po_name = parsed_order_document.get("ref")
        order = self.env["purchase.order"].search([("name", "=", po_name)])
        if not order:
            self.env["business.document.import"].user_error_wrap(
                method="process_data",
                data_dict=parsed_order_document,
                error_msg=self.env._(
                    "No purchase order found for name %(po_name)s.",
                    po_name=po_name,
                ),
                chatter_msg=[],
                raise_exception=True,
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
        if partner.commercial_partner_id != order.partner_id.commercial_partner_id:
            bdio.user_error_wrap(
                method="process_data",
                data_dict=parsed_order_document,
                error_msg=self.env._(
                    "The supplier of the imported OrderResponse (%(supplier)s) "
                    "is different from the supplier of the purchase order "
                    "(%(order_supplier)s).",
                    supplier=partner.commercial_partner_id.name,
                    order_supplier=order.partner_id.commercial_partner_id.name,
                ),
                chatter_msg=[],
                raise_exception=True,
            )
        if currency and currency != order.currency_id:
            bdio.user_error_wrap(
                method="process_data",
                data_dict=parsed_order_document,
                error_msg=self.env._(
                    "The currency of the imported OrderResponse (%(currency)s) "
                    "is different from the currency of the purchase order "
                    "(%(order_currency)s).",
                    currency=currency.name,
                    order_currency=order.currency_id.name,
                ),
                chatter_msg=[],
                raise_exception=True,
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
            bdio.user_error_wrap(
                method="process_data",
                data_dict=parsed_order_document,
                error_msg=self.env._("Unknown status '%(status)s'.", status=status),
                chatter_msg=[],
                raise_exception=True,
            )

        bdio.post_create_or_update(parsed_order_document, order)
        logger.info(
            "purchase.order ID %d updated via import of file %s.",
            order.id,
            self.filename,
        )
        order.message_post(
            body=self.env._(
                "This purchase order has been updated automatically"
                " via the import of OrderResponse file %(filename)s.",
                filename=self.filename,
            )
        )
        return order.get_formview_action()

    @api.model
    def _process_ack(self, purchase_order, parsed_order_document):
        if not purchase_order.supplier_ack_received_on:
            purchase_order.supplier_ack_received_on = fields.Datetime.now()

    @api.model
    def _process_rejected(self, purchase_order, parsed_order_document):
        parsed_order_document["chatter_msg"] = (
            parsed_order_document["chatter_msg"] or []
        )
        parsed_order_document["chatter_msg"].append(
            self.env._("PO cancelled by the supplier.")
        )
        purchase_order.button_cancel()

    @api.model
    def _process_accepted(self, purchase_order, parsed_order_document):
        parsed_order_document["chatter_msg"] = (
            parsed_order_document["chatter_msg"] or []
        )
        parsed_order_document["chatter_msg"].append(
            self.env._("PO confirmed by the supplier.")
        )
        purchase_order.button_approve()

    @api.model
    def _process_conditional(self, purchase_order, parsed_order_document):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        chatter = parsed_order_document["chatter_msg"] = (
            parsed_order_document["chatter_msg"] or []
        )
        chatter.append(self.env._("PO confirmed with amendment by the supplier."))
        lines = parsed_order_document["lines"]
        line_ids = [int(ln["line_id"]) for ln in lines if is_int(ln["line_id"])]
        if set(line_ids) != set(purchase_order.order_line.ids):
            self.env["business.document.import"].user_error_wrap(
                method="_process_conditional",
                data_dict=parsed_order_document,
                error_msg=self.env._(
                    "Unable to conditionally confirm the purchase order. \n"
                    "Line IDS into the parsed document differs from the "
                    "expected list of order line ids: \n "
                    "received: %(received_line_ids)s\n"
                    "expected: %(expected_line_ids)s\n",
                    received_line_ids=[ln["line_id"] for ln in lines],
                    expected_line_ids=purchase_order.order_line.ids,
                ),
                chatter_msg=chatter,
                raise_exception=True,
            )
        purchase_order.button_approve()
        # apply changes to the created moves...
        lines_by_id = {int(ln["line_id"]): ln for ln in lines}
        for order_line in purchase_order.order_line:
            line_info = lines_by_id[order_line.id]
            note = line_info.get("note")
            move = order_line.move_ids.filtered(
                lambda x: x.state not in ("cancel", "done")
            )
            if len(move) != 1:
                self.env["business.document.import"].user_error_wrap(
                    method="_process_conditional",
                    data_dict=parsed_order_document,
                    error_msg=self.env._(
                        "More than one move found for PO line.\n"
                        "Move IDs: %(move_ids)s\n"
                        "Line Info: %(line_info)s",
                        move_ids=move.ids,
                        line_info=line_info,
                    ),
                    chatter_msg=chatter,
                    raise_exception=True,
                )
            if note:
                move.description_picking += "\n" + note
            status = line_info["status"]
            if status == LINE_STATUS_ACCEPTED:
                continue
            if status == LINE_STATUS_REJECTED:
                order_line.move_ids._action_cancel()
            elif status == LINE_STATUS_AMEND:
                qty = line_info["qty"]
                backorder_qty = line_info["backorder_qty"]
                move_qty = move.product_qty
                if float_compare(qty, move_qty, precision_digits=precision) < 0:
                    self._check_picking_status(move.picking_id)
                    new_move_vals = move._split(move_qty - qty)
                    new_move = move.create(new_move_vals)
                    to_cancel = None
                    if backorder_qty:
                        note = note + "\n" if note else ""
                        note += self.env._(
                            "%(qty)s items should be delivered into a next delivery.",
                            qty=backorder_qty,
                        )
                        move.description_picking = note

                        # if the backorder qty is < than the remaining qty
                        # split and cancel the qty that will not be delivered
                        if (
                            float_compare(
                                backorder_qty,
                                new_move.product_qty,
                                precision_digits=precision,
                            )
                            < 0
                        ):
                            new_move._action_confirm()  # Cannot split draft moves
                            to_cancel_vals = new_move._split(
                                new_move.product_qty - backorder_qty
                            )
                            to_cancel = move.create(to_cancel_vals)
                    else:
                        to_cancel = new_move
                    if to_cancel:
                        to_cancel._action_cancel()
                        to_cancel.description_picking += "\n" + self.env._(
                            "No backorder planned by the supplier."
                        )
                    if new_move.state != "cancel":
                        # move the new move into a backorder picking to avoid
                        # that the scheduler merges the two moves into the same
                        # pack operation
                        self._add_move_to_backorder(new_move)

                    # Reset Operations
                    move.picking_id.action_assign()

    @api.model
    def _add_move_to_backorder(self, move):
        """
        Add the move the picking's backorder
        return the backorder associated to the current picking. If no backorder
        exists, create a new one.
        :param move:
        """
        StockPicking = self.env["stock.picking"]
        current_picking = move.picking_id
        backorder = StockPicking.search([("backorder_id", "=", current_picking.id)])
        if not backorder:
            date_done = current_picking.date_done
            move.picking_id._create_backorder(backorder_moves=move)
            # preserve date_done....
            current_picking.date_done = date_done
        else:
            move.write({"picking_id": backorder.id})
            backorder.action_confirm()
            backorder.action_assign()

    @api.model
    def _check_picking_status(self, picking):
        """
        The picking operations have already begun
        :param picking:
        :return:
        """
        if any(ml.picked for ml in picking.move_line_ids):
            raise ValidationError(
                self.env._(
                    "Some operations have already started! "
                    "Please validate or reset operations on "
                    "picking %(picking)s to ensure delivery slip to be computed.",
                    picking=picking.name,
                )
            )
