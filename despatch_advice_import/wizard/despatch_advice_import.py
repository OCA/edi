# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import mimetypes
from base64 import b64decode, b64encode

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare

logger = logging.getLogger(__name__)


class DespatchAdviceImport(models.TransientModel):
    _name = "despatch.advice.import"
    _description = "Despatch Advice Import from Files"

    document = fields.Binary(
        string="XML or PDF Despatch Advice",
        required=True,
        help="Upload an Despatch Advice file that you received from "
        "your supplier. Supported formats: XML and PDF "
        "(PDF with an embeded XML file).",
    )
    filename = fields.Char(string="File Name")
    allow_validate_over_qty = fields.Boolean(
        "Allow Validate Over Quantity", default=True
    )

    # Format of parsed despatch advice
    # {
    # 'ref': 'PO01234' # the buyer party identifier
    #                  # (specified into the Order document -> po's name)
    # 'despatch_advice_type_code': ' scheduled | delivered'
    # 'supplier': {'vat': 'FR25499247138'},
    # 'company': {'vat': 'FR12123456789'}, # Only used to check we are not
    #                                      # importing the quote in the
    #                                      # wrong company by mistake
    # 'estimated_delivery_date': '2020-11-20'
    # 'lines': [{
    #           'id': 123456,
    #           'qty': 2.5,
    #           'uom': {'unece_code': 'C62'},
    #           'backorder_qty: None  # if provided and qty != expected
    #                                 # the backorder qty will be delivered
    #                                 # in a next shipping
    #    }]

    @api.model
    def parse_despatch_advice(self, document, filename):
        if not document:
            raise UserError(_("Missing document file"))
        if not filename:
            raise UserError(_("Missing document filename"))
        filetype = mimetypes.guess_type(filename)[0]
        logger.debug("DespatchAdvice file mimetype: %s", filetype)
        if filetype in ["application/xml", "text/xml"]:
            try:
                xml_root = etree.fromstring(document)
            except Exception as err:
                raise UserError(_("This XML file is not XML-compliant")) from err
            if logger.isEnabledFor(logging.DEBUG):
                pretty_xml_string = etree.tostring(
                    xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True
                )
                logger.debug("Starting to import the following XML file:")
                logger.debug(pretty_xml_string)
            parsed_despatch_advice = self.parse_xml_despatch_advice(xml_root)
        elif filetype == "application/pdf":
            parsed_despatch_advice = self.parse_pdf_despatch_advice(document)
        else:
            raise UserError(
                _(
                    "This file '%s' is not recognised as XML nor PDF file. "
                    "Please check the file and it's extension."
                )
                % filename
            )
        logger.debug("Result of Despatch Advice parsing: ", parsed_despatch_advice)
        if "attachments" not in parsed_despatch_advice:
            parsed_despatch_advice["attachments"] = {}
        parsed_despatch_advice["attachments"][filename] = b64encode(document)
        if "chatter_msg" not in parsed_despatch_advice:
            parsed_despatch_advice["chatter_msg"] = []
        if parsed_despatch_advice.get("company") and not self.env.context.get(
            "edi_skip_company_check"
        ):
            self.env["business.document.import"]._check_company(
                parsed_despatch_advice["company"], parsed_despatch_advice["chatter_msg"]
            )
        defaults = self.env.context.get("despatch_advice_import__default_vals", {}).get(
            "despatch_advice", {}
        )
        parsed_despatch_advice.update(defaults)
        return parsed_despatch_advice

    @api.model
    def parse_xml_despatch_advice(self, xml_root):
        raise UserError(
            _(
                "This type of XML Order Response is not supported. Did you "
                "install the module to support this XML format?"
            )
        )

    @api.model
    def parse_pdf_despatch_advice(self, document):
        """
        Get PDF attachments, filter on XML files and call import_order_xml
        """
        xml_files_dict = self.get_xml_files_from_pdf(document)
        if not xml_files_dict:
            raise UserError(_("There are no embedded XML file in this PDF file."))
        for xml_filename, xml_root in xml_files_dict.items():
            logger.info("Trying to parse XML file %s", xml_filename)
            try:
                parsed_despatch_advice = self.parse_xml_despatch_advice(xml_root)
                return parsed_despatch_advice
            except Exception:
                continue
        raise UserError(
            _(
                "This type of XML Order Document is not supported. Did you "
                "install the module to support this XML format?"
            )
        )

    def process_document(self):
        self.ensure_one()
        parsed_order_document = self.parse_despatch_advice(
            b64decode(self.document), self.filename
        )
        self.process_data(parsed_order_document)

    def _collect_lines_by_id(self, lines_doc):
        lines_by_id = {}
        for line in lines_doc:
            line_id = int(line["order_line_id"])
            if line_id in lines_by_id:
                lines_by_id[line_id]["qty"] += line["qty"]
                lines_by_id[line_id]["backorder_qty"] += line["backorder_qty"]
                if "product_lot" in line:
                    lines_by_id[line_id]["product_lot"].append(line["product_lot"])
                    lines_by_id[line_id]["product_lot"] = list(
                        set(lines_by_id[line_id]["product_lot"])
                    )
                lines_by_id[line_id]["uom"]["unece_code"].append(
                    line["uom"]["unece_code"]
                )
                lines_by_id[line_id]["uom"]["unece_code"] = list(
                    set(lines_by_id[line_id]["uom"]["unece_code"])
                )
            else:
                lines_by_id[line_id] = line
                if "product_lot" in line:
                    lines_by_id[line_id]["product_lot"] = [
                        lines_by_id[line_id]["product_lot"]
                    ]
                lines_by_id[line_id]["uom"]["unece_code"] = [
                    lines_by_id[line_id]["uom"]["unece_code"]
                ]
        return lines_by_id

    def process_data(self, parsed_order_document):
        po_name = parsed_order_document.get("ref")

        lines_doc = parsed_order_document.get("lines")

        lines_by_id = self._collect_lines_by_id(lines_doc)

        lines = self.env["purchase.order.line"].browse(lines_by_id.keys())

        for line in lines:
            order = line.order_id
            line_info = lines_by_id.get(line.id)

            if line_info["ref"]:
                if order.name != line_info["ref"]:
                    raise UserError(
                        _("No purchase order found for name %s.") % line_info["ref"],
                    )
            else:
                if order.name != po_name:
                    raise UserError(_("No purchase order found for name %s.") % po_name)
            stock_moves = line.move_ids.filtered(
                lambda x: x.state not in ("cancel", "done")
            )
            moves_qty = sum(stock_moves.mapped("product_qty"))
            if line_info["qty"] == moves_qty:
                self._process_accepted(stock_moves, parsed_order_document)
            elif line_info["qty"] > moves_qty and self.allow_validate_over_qty:
                self._process_accepted(
                    stock_moves, parsed_order_document, forced_qty=line_info["qty"]
                )
            elif not line_info["qty"] and not line_info["backorder_qty"]:
                self._process_rejected(stock_moves, parsed_order_document)
            else:
                self._process_conditional(stock_moves, parsed_order_document, line_info)
        self._process_picking_done(lines[0].move_ids[0])

    def _process_picking_done(self, move):
        if all([line.quantity_done != 0 for line in move.picking_id.move_ids]):
            move.picking_id.button_validate()
        else:
            picking = move.picking_id
            picking.with_context(skip_backorder=True).button_validate()

    def _process_rejected(self, stock_moves, parsed_order_document):
        parsed_order_document["chatter_msg"] = parsed_order_document.get(
            "chatter_msg", []
        )
        parsed_order_document["chatter_msg"].append(
            _("Delivery cancelled by the supplier.")
        )

        stock_moves._action_cancel()

    def _process_accepted(self, stock_moves, parsed_order_document, forced_qty=False):
        parsed_order_document["chatter_msg"] = (
            parsed_order_document["chatter_msg"] or []
        )
        parsed_order_document["chatter_msg"].append(
            _("Delivery confirmed by the supplier.")
        )
        stock_moves._action_confirm()
        stock_moves._action_assign()
        for move in stock_moves:
            move.quantity_done = forced_qty or move.product_qty

    def _process_conditional(self, moves, parsed_order_document, line):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        chatter = parsed_order_document["chatter_msg"] = (
            parsed_order_document["chatter_msg"] or []
        )
        chatter.append(_("Delivery confirmed with amendment by the supplier."))

        qty = line["qty"]
        backorder_qty = line["backorder_qty"]
        moves_qty = sum(moves.mapped("product_qty"))

        if float_compare(qty, moves_qty, precision_digits=precision) >= 0:
            raise UserError(
                _("The product quantity is greater than the original product quantity")
            )

        # confirmed qty < ordered qty
        move_ids_to_backorder = []
        move_ids_to_cancel = []
        for move in moves:
            if (
                float_compare(qty, move.product_uom_qty, precision_digits=precision)
                >= 0
            ):
                # qty planned => qty into the stock move: Keep it
                qty -= move.product_uom_qty
                continue
            if (
                qty
                and float_compare(qty, move.product_uom_qty, precision_digits=precision)
                < 0
            ):
                # qty planned < qty into the stock move: Split it
                new_vals = move._split(move.product_uom_qty - qty)
                move.quantity_done = move.product_qty
                move = self.env["stock.move"].create(new_vals[0])

            qty -= move.product_uom_qty
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
                    backorder_qty, move.product_uom_qty, precision_digits=precision
                )
                < 0
            ):
                # backorder_qty < qty into the move -> split the move
                # and cancel remaining qty
                move._action_confirm(merge=False)
                new_vals = move._split(move.product_uom_qty - backorder_qty)
                move_ids_to_cancel.append(self.env["stock.move"].create(new_vals[0]).id)

            backorder_qty -= move.product_uom_qty
            move_ids_to_backorder.append(move.id)

        # cancel moves to cancel
        if move_ids_to_cancel:
            moves_to_cancel = self.env["stock.move"].browse(move_ids_to_cancel)
            moves_to_cancel._action_cancel()
        # move backorder moves to a backorder
        if move_ids_to_backorder:
            moves_to_backorder = self.env["stock.move"].browse(move_ids_to_backorder)
            for move in moves_to_backorder:
                move._action_confirm(merge=False)
