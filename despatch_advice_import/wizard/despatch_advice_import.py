# Copyright 2020 ACSONE SA/NV
# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import mimetypes
from base64 import b64decode, b64encode

from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare

logger = logging.getLogger(__name__)


class DespatchAdviceImport(models.TransientModel):
    """Import a supplier despatch advice and apply it on incoming receipts.

    The wizard parses a despatch advice document, matches it to purchase order
    lines, and then updates the related stock moves so the receipt reflects
    what the supplier confirmed, postponed, or canceled.
    """

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
    def parse_despatch_advice(self, document: bytes, filename: str):
        """Parse an uploaded XML or PDF document into a normalized dict.

        :param document: The raw content of the uploaded file, as bytes.
        :param filename: The name of the uploaded file, used to detect the file type.
        :return: A dict with the parsed despatch advice data, in a normalized format.
        """
        if not document:
            raise UserError(self.env._("Missing document file"))
        if not filename:
            raise UserError(self.env._("Missing document filename"))
        # Detect the file type from the uploaded filename extension to choose
        # the appropriate XML or PDF parsing flow.
        filetype = mimetypes.guess_type(filename)[0]
        logger.debug("DespatchAdvice file mimetype: %s", filetype)
        if filetype in ["application/xml", "text/xml"]:
            try:
                xml_root = etree.fromstring(document)
            except Exception as err:
                raise UserError(
                    self.env._("This XML file is not XML-compliant")
                ) from err
            if logger.isEnabledFor(logging.DEBUG):
                # Format the parsed XML for easier inspection in debug logs.
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
                self.env._(
                    "This file '%(filename)s' is not recognised as XML nor PDF file. "
                    "Please check the file and it's extension.",
                    filename=filename,
                )
            )
        logger.debug(
            "Result of Despatch Advice parsing: %(advice)s",
            {"advice": parsed_despatch_advice},
        )
        if "attachments" not in parsed_despatch_advice:
            parsed_despatch_advice["attachments"] = {}
        parsed_despatch_advice["attachments"][filename] = b64encode(document)
        chatter_msg = parsed_despatch_advice.get("chatter_msg")
        if chatter_msg is None:
            parsed_despatch_advice["chatter_msg"] = []
        elif isinstance(chatter_msg, (tuple, set)):
            parsed_despatch_advice["chatter_msg"] = list(chatter_msg)
        elif not isinstance(chatter_msg, list):
            parsed_despatch_advice["chatter_msg"] = [chatter_msg]
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
    def parse_xml_despatch_advice(self, xml_root: etree._Element):
        """Parse a despatch advice XML tree with a format-specific implementation.

        :param xml_root: The parsed XML root element to interpret.
        :return: A normalized dict containing the parsed despatch advice data.
        """
        raise UserError(
            self.env._(
                "This type of XML Order Response is not supported. Did you "
                "install the module to support this XML format?"
            )
        )

    @api.model
    def parse_pdf_despatch_advice(self, document: bytes):
        """Extract embedded XML files from a PDF and parse the first supported one.

        :param document: The raw content of the uploaded PDF file, as bytes.
        :return: A normalized dict containing the parsed despatch advice data.
        """
        xml_files_dict = self.get_xml_files_from_pdf(document)
        if not xml_files_dict:
            raise UserError(
                self.env._("There are no embedded XML file in this PDF file.")
            )
        for xml_filename, xml_root in xml_files_dict.items():
            logger.info("Trying to parse XML file %s", xml_filename)
            try:
                parsed_despatch_advice = self.parse_xml_despatch_advice(xml_root)
                return parsed_despatch_advice
            except Exception:
                continue
        raise UserError(
            self.env._(
                "This type of XML Order Document is not supported. Did you "
                "install the module to support this XML format?"
            )
        )

    @api.model
    def get_xml_files_from_pdf(self, document: bytes):
        """Return embedded XML attachments from a PDF as parsed XML roots.

        :param document: The raw content of the uploaded PDF file, as bytes.
        :return: A dict mapping embedded XML filenames to parsed XML root elements.
        """
        return self.env["pdf.xml.tool"].pdf_get_xml_files(document)

    def process_document(self):
        """Decode the uploaded file, parse it, and apply its stock impact."""
        self.ensure_one()
        parsed_order_document = self.parse_despatch_advice(
            b64decode(self.document), self.filename
        )
        self.process_data(parsed_order_document)

    def _collect_lines_by_id(self, lines_doc, key: str = "order_line_id"):
        """Aggregate imported lines by purchase order line id.

        A despatch advice may contain several entries for the same purchase
        line, so we consolidate quantities, lots, and UoM codes first.

        :param lines_doc: The parsed despatch advice lines to group and normalize.
        :param key: The line dict key containing the purchase order line identifier.
        :return: A dict mapping purchase order line ids to aggregated line data.
        """
        lines_by_id = {}
        for line in lines_doc:
            line = dict(line)
            line["qty"] = line.get("qty") or 0.0
            line["backorder_qty"] = line.get("backorder_qty") or 0.0
            line_id = int(line[key])
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

    def process_data(self, parsed_order_document: dict):
        """Apply the parsed despatch advice to the matching purchase moves.

        :param parsed_order_document: The normalized despatch advice data to apply.
        """
        po_name = parsed_order_document.get("ref")
        lines_doc = parsed_order_document.get("lines")
        lines_by_id = self._collect_lines_by_id(lines_doc)
        lines = self.env["purchase.order.line"].browse(list(lines_by_id))
        for line in lines:
            order = line.order_id
            line_info = lines_by_id.get(line.id)

            if line_info["ref"]:
                if order.name != line_info["ref"]:
                    raise UserError(
                        self.env._(
                            "No purchase order found for name %(name)s.",
                            name=line_info["ref"],
                        ),
                    )
            else:
                if order.name != po_name:
                    raise UserError(
                        self.env._(
                            "No purchase order found for name %(name)s.",
                            name=po_name,
                        )
                    )
            stock_moves = line.move_ids.filtered(
                lambda x: x.state not in ("cancel", "done")
            )
            moves_qty = sum(stock_moves.mapped("product_uom_qty"))
            # Compare the supplier-confirmed quantity with the open moves to
            # decide whether we fully accept, reject, or partially split them.
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
        if self.env.context.get("despatch_advice_import__picking_validation"):
            self._process_picking_done(lines[0].move_ids[0])

    def _process_picking_done(self, move: models.Model):
        """Validate the receipt once all line-level changes are applied.

        :param move: A stock move belonging to the picking that should be validated.
        :return: True when the picking only contains canceled moves, else None.
        """
        picking = move.picking_id
        if all(line.state == "cancel" for line in picking.move_ids):
            return True
        # skip backorder wizard
        picking.with_context(
            skip_immediate=True, skip_backorder=True, skip_sms=True, skip_expired=True
        ).button_validate()

    def _cancel_extra_moves(self, moves: models.Model):
        """Cancel moves while mimicking the usual backorder-cancel context.

        :param moves: The stock moves that should be canceled.
        """
        # Loose dependency with stock_picking_restrict_cancel_printed module
        # that checks we are canceling the backorder to allow move cancellation.
        # Mimic odoo setting this cancel_backorder context variable in this case.
        moves.with_context(cancel_backorder=True)._action_cancel()

    def _process_rejected(self, stock_moves: models.Model, parsed_order_document: dict):
        """Cancel remaining moves when the supplier cancels the delivery.

        :param stock_moves: The open stock moves linked to the purchase order line.
        :param parsed_order_document: The normalized despatch advice data being applied.
        """
        parsed_order_document["chatter_msg"] = parsed_order_document.get(
            "chatter_msg", []
        )
        parsed_order_document["chatter_msg"].append(
            self.env._("Delivery cancelled by the supplier.")
        )
        self._cancel_extra_moves(stock_moves)

    def _process_accepted(
        self,
        stock_moves: models.Model,
        parsed_order_document: dict,
        forced_qty=False,
    ):
        """Handle a delivery confirmed as-is by the supplier.

        The supplier delivers exactly what was ordered, or more when over-delivery
        is allowed. In both cases every move is marked done and picked so the
        validation wizard completes without prompting for a backorder.

        Without forced_qty the done quantity matches each move's planned demand.
        With forced_qty (over-delivery) that quantity replaces the planned demand
        on every move, recording what the supplier actually announced.

        :param stock_moves: The open stock moves linked to the purchase order line.
        :param parsed_order_document: The normalized despatch advice data being applied.
        :param forced_qty: The supplier-announced quantity to record when it exceeds
        the planned demand; False to use each move's planned quantity.
        """
        parsed_order_document["chatter_msg"] = (
            parsed_order_document["chatter_msg"] or []
        )
        parsed_order_document["chatter_msg"].append(
            self.env._("Delivery confirmed by the supplier.")
        )
        # merge=False: stock.move._merge_moves() looks for merge candidates
        # across the whole picking, not just stock_moves. Without this, an
        # exact-match line processed after another line was split on the
        # same picking (see _process_conditional/_split_move) would silently
        # re-merge that split back into one move, discarding the announced
        # backorder quantity.
        stock_moves._action_confirm(merge=False)
        stock_moves._action_assign()
        if self.env.context.get("despatch_advice_import__picking_validation"):
            for move in stock_moves:
                move._set_quantity_done(forced_qty or move.product_uom_qty)
                move.picked = True

    def _split_move(self, move: models.Model, qty_to_split):
        """Split a move and return the newly created split-off moves.

        :param move: The stock move that should be split.
        :param qty_to_split: The quantity to split off from the original move.
        :return: created stock moves, or an empty recordset if nothing was split.
        """
        split_moves_vals = move.with_context(cancel_backorder=False)._split(
            move.product_uom._compute_quantity(
                qty_to_split,
                move.product_id.uom_id,
                rounding_method="HALF-UP",
            )
        )
        if not split_moves_vals:
            return self.env["stock.move"]
        split_moves = self.env["stock.move"].create(split_moves_vals)
        split_moves.with_context(
            bypass_entire_pack=True, bypass_procurement_creation=True
        )._action_confirm(merge=False)
        return split_moves

    def _add_moves_to_backorder(self, moves: models.Model):
        """Prepare postponed quantities for validation backorder.

        :param moves: The stock moves that should remain open on a backorder.
        :return: The picking that will generate the backorder on validation.
        """
        moves.write({"picked": False})
        return moves[:1].picking_id

    def _process_conditional(
        self, moves: models.Model, parsed_order_document: dict, line: dict
    ):
        """Handle a partial delivery with backorder and cancellation logic.

        Confirmed quantities are marked done, postponed quantities are left
        unpicked for the validation backorder, and any remaining quantity is
        canceled.

        :param moves: The open stock moves linked to the purchase order line.
        :param parsed_order_document: The normalized despatch advice data being applied.
        :param line: The aggregated imported line data for the purchase order line.
        :return: A tuple of `(moves_to_backorder, moves_to_cancel)` recordsets.
        """
        digits = self.env["decimal.precision"].precision_get("Product Unit")
        chatter = parsed_order_document["chatter_msg"] = (
            parsed_order_document["chatter_msg"] or []
        )
        chatter.append(self.env._("Delivery confirmed with amendment by the supplier."))

        qty = line["qty"]
        backorder_qty = line["backorder_qty"]
        moves_qty = sum(moves.mapped("product_uom_qty"))

        if float_compare(qty, moves_qty, precision_digits=digits) >= 0:
            raise UserError(
                self.env._(
                    "The product quantity is greater than the original product quantity"
                )
            )

        # confirmed qty < ordered qty
        move_ids_to_backorder = []
        move_ids_to_cancel = []
        for move in moves:
            if move.product_uom.compare(qty, move.product_uom_qty) >= 0:
                # This move is fully confirmed for the current delivery.
                if self.env.context.get("despatch_advice_import__picking_validation"):
                    move._set_quantity_done(move.product_uom_qty)
                    move.picked = True
                qty -= move.product_uom_qty
                continue
            if qty and move.product_uom.compare(qty, move.product_uom_qty) < 0:
                # Only part of this move is delivered now, so we split the
                # remaining quantity into a new move for later handling.
                split_moves = self._split_move(move, move.product_uom_qty - qty)
                if self.env.context.get("despatch_advice_import__picking_validation"):
                    move._set_quantity_done(move.product_uom_qty)
                    move.picked = True
                move = split_moves[:1]
                qty = 0.0
            if not backorder_qty:
                # No postponed quantity was announced,
                # so the remaining move is canceled.
                move_ids_to_cancel.append(move.id)
                continue
            # The remaining quantity is postponed by the supplier and should
            # stay open on a backorder picking.
            if move.product_uom.compare(backorder_qty, move.product_uom_qty) < 0:
                # Only part of this move belongs to the backorder; the extra
                # quantity is split off and canceled.
                split_moves = self._split_move(
                    move, move.product_uom_qty - backorder_qty
                )
                move_ids_to_cancel += split_moves.ids

            backorder_qty -= move.product_uom_qty
            move_ids_to_backorder.append(move.id)

        # move backorder moves to a backorder
        if move_ids_to_backorder:
            moves_to_backorder = self.env["stock.move"].browse(move_ids_to_backorder)
            self._add_moves_to_backorder(moves_to_backorder)
        else:
            moves_to_backorder = self.env["stock.move"]
        # cancel moves to cancel
        if move_ids_to_cancel:
            moves_to_cancel = self.env["stock.move"].browse(move_ids_to_cancel)
            self._cancel_extra_moves(moves_to_cancel)
        else:
            moves_to_cancel = self.env["stock.move"]
        return moves_to_backorder, moves_to_cancel
