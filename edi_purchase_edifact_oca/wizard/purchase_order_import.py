# Copyright 2024 Trobz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import mimetypes
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

        existing_quotations = self.env["purchase.order"].search(
            [
                ("state", "in", ("draft", "sent")),
                ("name", "=", parsed_order["order_ref"]),
            ]
        )
        if existing_quotations:
            return self.update_purchase_order(existing_quotations[0], parsed_order)
        else:
            raise UserError(
                _("Purchase Order Id {id} is not found").format(
                    id=parsed_order["order_ref"]
                )
            )

    @api.model
    def parse_edifact_order(self, filecontent):
        edifact_model = self.env["base.edifact"]
        interchange = edifact_model._loads_edifact(filecontent)
        header = interchange.get_header_segment()
        # > UNB segment: [['UNOA', '2'], ['5450534000000', '14'],
        # ['8435337000003', '14'], ['230306', '0435'], '5506']

        msg_type, _ = edifact_model._get_msg_type(interchange)

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
        }
        parties = self._prepare_edifact_parties(interchange)
        order_dict = {
            **rd,
            **self._prepare_edifact_dates(interchange),
            **self._prepare_edifact_currencies(interchange),
            **parties,
        }
        lines = self._prepare_edifact_lines(interchange)
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
                # dates.setdefault("delivery_detail",{})
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
    def _prepare_edifact_lines(self, interchange):
        edifact_model = self.env["base.edifact"]
        bdio = self.env["business.document.import"]
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
            if i[1] == "79":
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

            # Check product
            bdio._match_product(line["product"], "")

            price_unit = edifact_model.map2odoo_unit_price(priseg)
            # If the product price is not provided,
            # the price will be taken from the system
            if price_unit != 0.0:
                line["price_unit"] = price_unit
            description = edifact_model.map2odoo_description(imdseg)
            if description:
                line["name"] = description

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

    @api.model
    def update_order_lines(self, parsed_order, order):
        chatter = parsed_order["chatter_msg"]
        polo = self.env["purchase.order.line"]
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
                    "qty": oline.product_uom_qty,
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
        for oline, cdict in compare_res["to_update"].items():
            write_vals = {}
            if cdict.get("qty"):
                chatter.append(
                    _(
                        "The quantity has been updated on the order line "
                        "with product '%(product)s' from %(qty0)s to %(qty1)s %(uom)s"
                    ).format(
                        product=oline.product_id.display_name,
                        qty0=cdict["qty"][0],
                        qty1=cdict["qty"][1],
                        uom=oline.product_uom.name,
                    )
                )
                write_vals["product_uom_qty"] = cdict["qty"][1]
                write_vals["product_qty"] = cdict["qty"][1]
                write_vals.update(self._prepare_update_order_line_vals(cdict))
            if write_vals:
                oline.write(write_vals)
        if compare_res["to_remove"]:
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
        if compare_res["to_add"]:
            to_create_label = []
            for add in compare_res["to_add"]:
                line_vals = self._prepare_create_order_line(
                    add["product"], add["uom"], order, add["import_line"]
                )
                line_vals["date_planned"] = parsed_order["delivery_detail"][
                    "date_planned"
                ]
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
        return True

    @api.model
    def _prepare_update_order_vals(self, parsed_order):
        bdio = self.env["business.document.import"]
        partner = bdio._match_partner(
            parsed_order["partner"],
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
        self.update_order_lines(parsed_order, order)
        bdio.post_create_or_update(parsed_order, order)
        logger.info(
            "Quotation ID %d updated via import of file %s",
            order.id,
            self.order_filename,
        )
        order.message_post(
            body=_(
                "This quotation has been updated automatically via the import of "
                "file %s"
            )
            % self.order_filename
        )
        if parsed_order["msg_type"] == "DESADV":
            order.button_confirm()
        action = self.env.ref("purchase.purchase_form_action").read()[0]
        action.update(
            {
                "view_mode": "form,tree,calendar,graph",
                "views": False,
                "view_id": False,
                "res_id": order.id,
            }
        )
        return action
