# Copyright 2024 Trobz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import mimetypes
import json
from base64 import b64decode, b64encode
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config, float_is_zero

logger = logging.getLogger(__name__)


class PurchaseOrderImport(models.TransientModel):
    _name = "purchase.order.import"
    _description = "Purchase Order Import from Files"

    partner_id = fields.Many2one("res.partner", string="Customer")

    import_type = fields.Selection(
        [("edifact", "EDIFACT")],
        required=True,
        default="edifact",
        help="Select a type which you want to import",
    )

    order_file = fields.Binary(
        string="Request for Quotation or Order",
        required=True,
    )
    order_filename = fields.Char(string="Filename")

    def _get_supported_types(self):
        supported_types = {
            "edifact": ("text/plain", None),
        }
        return supported_types

    def _parse_file(self, filename, filecontent):
        assert filename, "Missing filename"
        assert filecontent, "Missing file content"
        filetype = mimetypes.guess_type(filename)
        logger.debug("Order file mimetype: %s", filetype)
        mimetype = filetype[0]
        supported_types = self._get_supported_types()
        # Check if the selected import type is supported
        if self.import_type not in supported_types:
            raise UserError(_("Please select a valid import type before importing!"))

        # Check if the detected MIME type is supported for the selected import type
        if mimetype not in supported_types[self.import_type]:
            raise UserError(
                _(
                    "This file '%(filename)s' is not recognized as a %(type)s file. "
                    "Please check the file and its extension.",
                    filename=filename,
                    type=self.import_type.upper(),
                )
            )
        if hasattr(self, "parse_%s_order" % self.import_type):
            return getattr(self, "parse_%s_order" % self.import_type)(filecontent)
        else:
            raise UserError(
                _(
                    "This Import Type is not supported. Did you install "
                    "the module to support this type?"
                )
            )

    @api.model
    def parse_order(self, order_file, order_filename):
        parsed_order = self._parse_file(order_filename, order_file)
        logger.debug("Result of order parsing: %s", parsed_order)
        defaults = (
            ("attachments", {}),
            ("chatter_msg", []),
        )
        for key, val in defaults:
            parsed_order.setdefault(key, val)

        parsed_order["attachments"][order_filename] = b64encode(order_file)
        if (
            parsed_order.get("company")
            and not config["test_enable"]
            and not self._context.get("edi_skip_company_check")
        ):
            self.env["business.document.import"]._check_company(
                parsed_order["company"], parsed_order["chatter_msg"]
            )
        return parsed_order

    def import_order_button(self):
        self.ensure_one()
        order_file_decoded = b64decode(self.order_file)
        parsed_order = self.parse_order(order_file_decoded, self.order_filename)

        if not parsed_order.get("lines"):
            raise UserError(_("This order doesn't have any line !"))
        order = parsed_order.get("order", False)
        if order and not order.picking_ids.filtered(
            lambda picking: picking.state not in ("done", "cancel")
        ):
            order = order.copy(default={"order_line": [(5, 0, 0)]})
            parsed_order["order"] = order

        return self.update_purchase_order(order, parsed_order)

    @api.model
    def parse_edifact_order(self, filecontent):
        edifact_model = self.env["base.edifact"]
        interchange = edifact_model._loads_edifact(filecontent)
        header = interchange.get_header_segment()
        # > UNB segment: [['UNOA', '2'], ['5450534000000', '14'],
        # ['8435337000003', '14'], ['230306', '0435'], '5506']

        msg_type, __ = edifact_model._get_msg_type(interchange)

        supported = ["ORDERS", "DESADV"]
        if msg_type not in supported:
            raise UserError(
                _("{msg_type} document is not a Purchase Order document").format(
                    msg_type=msg_type
                )
            )

        bgm = interchange.get_segment("BGM")
        # Supplier PO number
        # BGM segment: ['220', '1LP6WZGF', '9']
        order_ref = bgm[1]

        rd = {
            # Supplier PO number
            "order_ref": order_ref,
            "edi_ctx": {"sender": header[1], "recipient": header[2]},
            "msg_type": msg_type,
            "reception_lines": len(list(interchange.get_segments("LIN"))),
        }
        parties = self._prepare_edifact_parties(interchange)
        order_dict = {
            **rd,
            **self._prepare_edifact_dates(interchange),
            **self._prepare_edifact_currencies(interchange),
            **parties,
        }

        existing_quotations = self.env["purchase.order"].search(
            [
                ("state", "=", "purchase"),
                ("name", "=", order_dict["order_ref"]),
            ]
        )
        if existing_quotations:
            order_dict["order"] = existing_quotations[0]
        else:
            raise UserError(
                _("Purchase Order Id {id} is not found").format(
                    id=order_dict["order_ref"]
                )
            )

        lines = self._prepare_edifact_lines(interchange, order_dict)
        if lines:
            order_dict["lines"] = lines
        return order_dict

    @api.model
    def _prepare_edifact_parties(self, interchange):
        references = self._prepare_edifact_references(interchange)
        parties = self._prepare_edifact_name_and_address(interchange)
        if references.get("vat") and parties.get("invoice_to"):
            # just for check vat
            if parties["invoice_to"].get("partner"):
                parties["invoice_to"]["partner"]["rff_va"] = references["vat"]
        if parties.get("invoice_to") and parties["invoice_to"].get("partner"):
            newpartner = parties["invoice_to"]["partner"].copy()
            if parties.get("partner") and parties["partner"].get("gln"):
                # To see if NAD_BY is different NAD_IV
                newpartner["gln_by"] = parties["partner"]["gln"]
            parties["partner"] = newpartner
        # add context information
        for pval in parties.values():
            partner_dict = pval.get("partner", pval)
            partner_dict["edi_ctx"] = {
                "order_filename": self.order_filename,
            }
            if references.get("vat"):
                partner_dict["edi_ctx"]["rff_va"] = references["vat"]
        if parties.get("company"):
            parties["company"]["edi_ctx"]["vendor_code"] = references.get("vendor_code")
        if references.get("order_ref"):
            parties["order_ref"] = references["order_ref"]
        return parties

    @api.model
    def _prepare_edifact_dates(self, interchange):
        dates = defaultdict(dict)
        edifact_model = self.env["base.edifact"]
        for seg in interchange.get_segments("DTM"):
            date_meaning_code = seg[0][0]
            if date_meaning_code == "137":
                dates["date"] = edifact_model.map2odoo_date(seg[0])
            elif date_meaning_code == "63":
                # latest delivery date
                dates["delivery_detail"]["validity_date"] = edifact_model.map2odoo_date(
                    seg[0]
                )
            elif date_meaning_code == "2":
                # Date planned
                dates["delivery_detail"]["date_planned"] = edifact_model.map2odoo_date(
                    seg[0]
                )

        return dates

    @api.model
    def _prepare_edifact_references(self, interchange):
        """
        RFF segment: [['CR', 'IK142']]
        """
        refs = {}
        for seg in interchange.get_segments("RFF"):
            reference = seg[0]
            reference_code = reference[0]
            if reference_code == "ADE":
                # ['firstorder','backorder','advantage','nyp']
                refs["account_reference"] = reference[1]
            elif reference_code == "CR":
                # Customer reference Number
                refs["vendor_code"] = reference[1]
            elif reference_code == "PD":
                # Promotion Deal Number
                # Number assigned by a vendor to a special promotion activity
                refs["promotion_number"] = reference[1]
            elif reference_code == "VA":
                # Unique number assigned by the relevant tax authority to identify a
                # party for use in relation to Value Added Tax (VAT).
                refs["vat"] = reference[1]
            elif reference_code == "ON":
                # Order reference number
                refs["order_ref"] = reference[1]

        return refs

    @api.model
    def _prepare_edifact_name_and_address(self, interchange):
        nads = {}
        edifact_model = self.env["base.edifact"]
        for seg in interchange.get_segments("NAD"):
            reference_code = seg[0]
            if reference_code == "BY":
                # NAD segment: ['BY', ['5450534001649', '', '9']]
                # Customer (Buyer's GLN)
                nads["partner"] = edifact_model.map2odoo_partner(seg)
            elif reference_code == "SU":
                # Our number of Supplier's GLN
                # Can be used to check that we are not importing the order
                # in the wrong company by mistake
                nads["company"] = edifact_model.map2odoo_partner(seg)
            elif reference_code == "DP":
                # Delivery Party
                nads["ship_to"] = edifact_model.map2odoo_address(seg)
            elif reference_code == "IV":
                # Invoice Party
                nads["invoice_to"] = edifact_model.map2odoo_address(seg)
        return nads

    @api.model
    def _prepare_edifact_currencies(self, interchange):
        currencies = {}
        edifact_model = self.env["base.edifact"]
        for seg in interchange.get_segments("CUX"):
            usage_code = seg[0][0]
            if usage_code == "2":
                currencies["currency"] = edifact_model.map2odoo_currency(seg[0])
        return currencies

    @api.model
    def _prepare_edifact_lines(self, interchange, order_dict):
        edifact_model = self.env["base.edifact"]
        bdio = self.env["business.document.import"]
        order = order_dict["order"]
        partner_id_number = order_dict["company"]
        order_dict["unknown_products"] = []
        partner = bdio._match_partner(
            partner_id_number,
            "",
            partner_type="customer",
        )
        lines = []
        pia_list = []
        qty_list = []
        pri_list = []
        imd_list = []

        for i in interchange.get_segments("PIA"):
            if i[1][1] == "SA":
                pia_list.append(i)
        for i in interchange.get_segments("QTY"):
            if i[0][0] == "21" or i[0][0] == "12":
                qty_list.append(i)
        for i in interchange.get_segments("PRI"):
            pri_list.append(i)
        for i in interchange.get_segments("IMD"):
            if i[0] == "A" and i[1] == "":
                imd_list.append(i)

        for linseg in interchange.get_segments("LIN"):

            piaseg = pia_list.pop(0) if pia_list else None
            qtyseg = qty_list.pop(0) if qty_list else None
            priseg = pri_list.pop(0) if pri_list else None
            imdseg = imd_list.pop(0) if imd_list else None

            line = {
                "sequence": int(linseg[0]),
                "product": edifact_model.map2odoo_product(linseg, piaseg),
                "qty": edifact_model.map2odoo_qty(qtyseg),
            }

            price_unit = edifact_model.map2odoo_unit_price(priseg)
            # If the product price is not provided,
            # the price will be taken from the system
            if price_unit != 0.0:
                line["price_unit"] = price_unit

            description = edifact_model.map2odoo_description(imdseg)
            if description:
                line["name"] = description

            try:
                # Check product
                bdio._match_product(line["product"], "")
            except UserError as error:
                if (
                    order
                    and
                    partner.edifact_despatch_advice_ignore_lines_with_unknown_products
                ):
                    order.message_post(body=_(error.name))
                    order_dict["unknown_products"].append(line)
                    continue
                else:
                    raise error

            lines.append(line)

        return lines

    @api.model
    def _prepare_create_order_line(self, product, uom, order, import_line):
        """the 'order' arg can be a recordset (in case of an update of a purchase order)
        or a dict (in case of the creation of a new purchase order)"""
        polo = self.env["purchase.order.line"]
        vals = {}
        # Ensure the company is loaded before we play onchanges.
        # Yes, `company_id` is related to `order_id.company_id`
        # but when we call `play_onchanges` it will be empty
        # w/out this precaution.
        company_id = self._prepare_order_line_get_company_id(order)
        vals.update(
            {
                "name": product.display_name,
                "product_id": product.id,
                "product_uom_qty": import_line["qty"],
                "product_qty": import_line["qty"],
                "product_uom": uom.id,
                "company_id": company_id,
                "order_id": order.id,
            }
        )
        # Handle additional fields dynamically if available.
        # This way, if you add a field to a record
        # and it's value is injected by a parser
        # you won't have to override `_prepare_create_order_line`
        # to let it propagate.
        for k, v in import_line.items():
            if k not in vals and k in polo._fields:
                vals[k] = v

        defaults = self.env.context.get("purchase_order_import__default_vals", {}).get(
            "lines", {}
        )
        vals.update(defaults)
        return vals

    def _prepare_update_order_line_vals(self, change_dict):
        # Allows other module to update some fields on the line
        return {}

    def _prepare_order_line_get_company_id(self, order):
        company_id = self.env.user.company_id
        if isinstance(order, models.Model):
            company_id = order.company_id.id
        elif isinstance(order, dict):
            company_id = order.get("company_id") or company_id
        return company_id

    def _add_order_line_from_compare_res(self, order, compare_res, parsed_order):
        chatter = parsed_order["chatter_msg"]
        polo = self.env["purchase.order.line"]
        to_create_label = []
        for add in compare_res["to_add"]:
            line_vals = self._prepare_create_order_line(
                add["product"], add["uom"], order, add["import_line"]
            )
            line_vals["date_planned"] = parsed_order["delivery_detail"]["date_planned"]
            new_line = polo.create(line_vals)
            to_create_label.append(
                "%s %s x %s"
                % (
                    new_line.product_uom_qty,
                    new_line.product_uom.name,
                    new_line.name,
                )
            )
        chatter.append(
            _("%(orders)s new order line(s) created: %(label)s").format(
                orders=len(compare_res["to_add"]), label=", ".join(to_create_label)
            )
        )
        # Update quantity_done with product_uom_qty with PO created based on
        # information from Despatch Advice
        if order.state not in ["purchase", "done", "cancel"]:
            order.with_context(skip_send_edifact=True).button_confirm()
            for picking in order.picking_ids.filtered(
                lambda p: p.state not in ["done", "cancel"]
            ):
                for move in picking.move_lines:
                    move.quantity_done = move.product_uom_qty
                self._update_qty_done_package(picking.move_lines)

    def _remove_order_line_from_compare_res(self, compare_res, parsed_order):
        chatter = parsed_order["chatter_msg"]
        to_remove_label = [
            "%s %s x %s"
            % (line.product_uom_qty, line.product_uom.name, line.product_id.name)
            for line in compare_res["to_remove"]
        ]
        chatter.append(
            _("{orders} order line(s) deleted: {label}").format(
                orders=len(compare_res["to_remove"]),
                label=", ".join(to_remove_label),
            )
        )
        compare_res["to_remove"].unlink()

    @api.model
    def update_order_lines(self, parsed_order, order):
        chatter = parsed_order["chatter_msg"]
        qty_diff_list = parsed_order["qty_diff"] = []
        dpo = self.env["decimal.precision"]
        bdio = self.env["business.document.import"]
        qty_prec = dpo.precision_get("Product UoS")
        existing_lines = []
        for oline in order.order_line:
            # compute price unit without tax
            price_unit = 0.0
            if not float_is_zero(oline.product_uom_qty, precision_digits=qty_prec):
                qty = float(oline.product_uom_qty)
                price_unit = oline.price_subtotal / qty
            existing_lines.append(
                {
                    "product": oline.product_id or False,
                    "name": oline.name,
                    # Assign to 0 to get update qty data in `compare_res``
                    "qty": 0,
                    "uom": oline.product_uom,
                    "line": oline,
                    "price_unit": price_unit,
                }
            )
        compare_res = bdio.compare_lines(
            existing_lines,
            parsed_order["lines"],
            chatter,
            qty_precision=qty_prec,
            seller=False,
        )

        # NOW, we start to write/delete/create the order lines
        number_line_updated = 0
        picking_dict = {}
        for oline, cdict in compare_res["to_update"].items():
            write_vals = {}
            if cdict.get("qty"):
                write_vals.update(self._prepare_update_order_line_vals(cdict))
                if oline.product_id.type == "product":
                    delivery_qty = cdict["qty"][1]
                    if oline.product_qty != delivery_qty + oline.qty_received:
                        qty_diff_list.append(
                            {
                                "message": "Mismatch between ordered quantity"
                                " ({}) and quantity being delivered ({})".format(
                                    oline.product_qty, delivery_qty
                                ),
                                "Order Line Info": {
                                    "id": oline.id,
                                    "product_id": oline.product_id.id,
                                    "barcode": oline.product_id.barcode,
                                    "default_code": oline.product_id.default_code,
                                    "description": oline.name,
                                    "product_qty": oline.product_qty,
                                    "qty_recieved": oline.qty_received,
                                    "incoming_qty": delivery_qty,
                                },
                            }
                        )
                    updated_picking_dict = self._update_stock_moves(
                        oline, delivery_qty, picking_dict
                    )
                    if updated_picking_dict:
                        picking_dict = updated_picking_dict
                        number_line_updated += 1

            if write_vals:
                oline.write(write_vals)
        for picking, move_ids in picking_dict.items():
            message = (
                "Record has been updated automatically via the import Despatch Advice."
                f" Done quantities were updated on {len(move_ids)} lines out of "
                f"the {len(picking.move_line_ids)} Reception lines."
            )
            picking.message_post(body=_(message))

        if compare_res["to_remove"] and order.state not in ["purchase", "done"]:
            self._remove_order_line_from_compare_res(compare_res, parsed_order)

        if compare_res["to_add"]:
            if order.state in ["purchase", "done"]:
                sub_order = order.copy(default={"order_line": [(5, 0, 0)]})
                order.message_post(
                    body=_(
                        "Received some unexpected products. "
                        "Created a new Purchase Order for it in "
                        "<a href=# data-oe-model=purchase.order data-oe-id=%d>%s</a>."
                    )
                    % (sub_order.id, sub_order.name)
                )
                order = sub_order
            self._add_order_line_from_compare_res(order, compare_res, parsed_order)
        return number_line_updated

    def _update_qty_done_package(self, moves):
        if hasattr(moves, "qty_done_package"):
            for move in moves:
                if (
                    move.purchase_line_id
                    and move.quantity_done > 0
                    and move.package_qty
                ):
                    move.qty_done_package = move.quantity_done / move.package_qty
        return moves

    @api.model
    def _update_stock_moves(self, order_line, new_qty, picking_dict=None):
        if picking_dict is None:
            picking_dict = {}
        moves = order_line.move_ids.filtered(
            lambda move: move.state not in ("done", "cancel", "draft")
        )
        if not moves:
            raise UserError(f"No valid moves to update for the line {order_line.name}")
        total_qty_update = (
            new_qty - order_line.qty_received - sum(moves.mapped("quantity_done"))
        )
        if total_qty_update <= 0:
            order_line.order_id.message_post(
                body=_(
                    "The quantity delivered for product "
                    "<a href=# data-oe-model=product.product data-oe-id=%d>%s</a> "
                    "is less than or equal to the quantity received."
                )
                % (order_line.product_id.id, order_line.product_id.name)
            )
        if total_qty_update > 0:
            for move in moves:
                if total_qty_update <= 0:
                    break

                available_qty = move.product_uom_qty - move.quantity_done

                if available_qty > 0:
                    if total_qty_update >= available_qty:
                        move.quantity_done = move.product_uom_qty
                        total_qty_update -= available_qty
                    else:
                        move.quantity_done += total_qty_update
                        total_qty_update = 0

                    if not picking_dict.get(move.picking_id, False):
                        picking_dict[move.picking_id] = []
                    picking_dict[move.picking_id].append(move.id)

            self._update_qty_done_package(moves)

            # Create new stock.move if still available
            if total_qty_update > 0:
                new_move = moves[-1].copy(
                    {
                        "product_uom_qty": total_qty_update,
                        "quantity_done": total_qty_update,
                        "state": "draft",
                    }
                )
                new_move = self._update_qty_done_package(new_move._action_confirm())
                new_move._action_assign()

            # Return the pickings with updated moves to print the message
            return picking_dict
        return False

    @api.model
    def _prepare_update_order_vals(self, parsed_order):
        bdio = self.env["business.document.import"]
        partner = bdio._match_partner(
            parsed_order["company"],
            parsed_order["chatter_msg"],
            partner_type="customer",
        )
        vals = {"partner_id": partner.id}
        return vals

    def update_purchase_order(self, order, parsed_order):
        self.ensure_one()
        bdio = self.env["business.document.import"]
        currency = bdio._match_currency(
            parsed_order.get("currency"), parsed_order["chatter_msg"]
        )
        if currency != order.currency_id:
            raise UserError(
                _(
                    "The currency of the imported order {old} is different from "
                    "the currency of the existing order {new}"
                ).format(
                    old=currency.name,
                    new=order.currency_id.name,
                )
            )
        vals = self._prepare_update_order_vals(parsed_order)
        if vals:
            order.write(vals)
        number_line_updated = self.update_order_lines(parsed_order, order)
        bdio.post_create_or_update(parsed_order, order)
        logger.info(
            "Order ID %d updated via import of file %s",
            order.id,
            self.order_filename,
        )
        action = self.env.ref("purchase.purchase_form_action").read()[0]
        action.update(
            {
                "view_mode": "form,tree,calendar,graph",
                "views": False,
                "view_id": False,
                "res_id": order.id,
                "unknown_products": parsed_order["unknown_products"],
                "qty_diff": parsed_order["qty_diff"],
                "reception_lines": parsed_order["reception_lines"],
                "number_line_updated": number_line_updated,
            }
        )
        message = self._create_expected_reception_message(action)
        order.message_post(body=_(message))

        return action

    def _create_expected_reception_message(self, action):
        message = """
            \nThis order has been updated automatically via the import of file {}
            \nDone quantities were updated on {} lines out of the {} Reception lines
        """.format(
            self.order_filename,
            action.get("number_line_updated", 0),
            action.get("reception_lines", 0),
        )

        unknown_products = action.get("unknown_products", False)
        if unknown_products:
            message += "\nUnknow Product: \n"
            message += "  * " + "\n  * ".join(
                json.dumps(rec, indent=4) for rec in unknown_products
            )
        qty_diff = action.get("qty_diff", False)
        if qty_diff:
            message += "\nDifference of Qty: \n"
            message += "  * " + "\n  * ".join(
                json.dumps(rec, indent=4) for rec in qty_diff
            )
        return message
