import json
import logging
import os
from base64 import b64decode
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class SaleOrderImportEdifact(models.TransientModel):
    _name = "sale.order.import"
    _inherit = ["sale.order.import", "base.edifact"]

    state = fields.Selection(
        selection_add=[("tech", "Technical")], ondelete={"tech": "set default"}
    )
    parsed_json = fields.Text()

    @property
    def edifact_ok(self):
        conf_ext = self.env.context.get("file_ext", "txt,d96a")
        extensions = conf_ext.split(",")
        ok = False
        if self.order_filename:
            path, ext = os.path.splitext(self.order_filename)
            ok = ext and ext[1:] in extensions
            if not ok and self.order_file:
                ok = b64decode(self.order_file[:4]) == b"UNB"
        return ok

    @api.onchange("order_file")
    def order_file_change(self):
        if self.edifact_ok:
            self.csv_import = False
            self.doc_type = self.env.context.get("doc_type", "rfq")
            self.price_source = "order"
        else:
            res = super(SaleOrderImportEdifact, self).order_file_change()
            if isinstance(res, dict):
                return res

    def parse_order_button(self):
        self.ensure_one()
        order_file_decoded = b64decode(self.order_file)
        parsed_obj = dict(edifact=None, order=None)
        if self.edifact_ok:
            parsed_obj["edifact"] = self.pydifact_obj(order_file_decoded)

        parsed_order = self.parse_order(
            order_file_decoded, self.order_filename, self.partner_id
        )
        del parsed_order["attachments"]
        parsed_obj["order"] = parsed_order
        self.write(
            {
                "parsed_json": json.dumps(parsed_obj, indent=4, default=str),
                "state": "tech",
            }
        )
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "sale_order_import.sale_order_import_action"
        )
        action["res_id"] = self.id
        return action

    # Parser hook
    def _parse_file(self, filename, filecontent, detect_doc_type=False):
        "Called from parse_order()"
        parsed_order = super(SaleOrderImportEdifact, self)._parse_file(
            filename, filecontent, detect_doc_type
        )
        if not parsed_order and self.edifact_ok:
            self.env.context.get("release", "d96a")
            interchange = self._loads_edifact(filecontent)
            parsed_order = self.parse_edifact_sale_order(interchange)
        return parsed_order

    @api.model
    def parse_edifact_sale_order(self, interchange):
        # https://github.com/nerdocs/pydifact/blob/master/pydifact/segmentcollection.py
        header = interchange.get_header_segment()
        # > UNB segment: [['UNOA', '2'], ['5450534000000', '14'],
        # ['8435337000003', '14'], ['230306', '0435'], '5506']

        msg_type, msg_type_release = self._get_msg_type(interchange)
        supported = ["ORDERS"]
        if msg_type not in supported:
            raise UserError(_("%s document is not a Sale Order document"))

        doc_type = self.env.context.get("doc_type", "order")

        bgm = interchange.get_segment("BGM")
        # Customer PO number
        # BGM segment: ['220', '1LP6WZGF', '9']
        order_ref = bgm[1]

        rd = {
            "doc_type": doc_type,
            # Customer PO number
            "order_ref": order_ref,
            "edi_ctx": {"sender": header[1], "recipient": header[2]},  # header[1][0]
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
                "rff_va": references["vat"],
            }
        if parties.get("company"):
            parties["company"]["edi_ctx"]["vendor_code"] = references.get("vendor_code")
        return parties

    @api.model
    def _prepare_edifact_dates(self, interchange):
        dates = defaultdict(dict)
        for seg in interchange.get_segments("DTM"):
            date_meaning_code = seg[0][0]
            if date_meaning_code == "137":
                dates["date"] = self.map2odoo_date(seg[0])
            elif date_meaning_code == "63":
                # latest delivery date
                # dates.setdefault("delivery_detail",{})
                dates["delivery_detail"]["validity_date"] = self.map2odoo_date(seg[0])
            elif date_meaning_code == "64":
                # earliest delivery date
                dates["delivery_detail"]["commitment_date"] = self.map2odoo_date(seg[0])

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

        return refs

    @api.model
    def _prepare_edifact_name_and_address(self, interchange):
        nads = {}
        for seg in interchange.get_segments("NAD"):
            reference_code = seg[0]
            if reference_code == "BY":
                # NAD segment: ['BY', ['5450534001649', '', '9']]
                # Customer (Buyer's GLN)
                nads["partner"] = self.map2odoo_partner(seg)
            elif reference_code == "SU":
                # Our number of Supplier's GLN
                # Can be used to check that we are not importing the order
                # in the wrong company by mistake
                nads["company"] = self.map2odoo_partner(seg)
            elif reference_code == "DP":
                # Delivery Party
                nads["ship_to"] = self.map2odoo_address(seg)
            elif reference_code == "IV":
                # Invoice Party
                nads["invoice_to"] = self.map2odoo_address(seg)
        return nads

    @api.model
    def _prepare_edifact_currencies(self, interchange):
        currencies = {}
        for seg in interchange.get_segments("CUX"):
            usage_code = seg[0]
            if usage_code == "2":
                currencies["currency"] = self.map2odoo_currency(seg)
        return currencies

    @api.model
    def _prepare_edifact_lines(self, interchange):
        lines = []
        zipsegments = zip(
            interchange.get_segments("LIN"),
            interchange.get_segments("QTY"),
            interchange.get_segments("PRI"),
        )

        for linseg, qtyseg, priseg in zipsegments:
            lines.append(
                {
                    "sequence": int(linseg[0]),
                    "product": self.map2odoo_product(linseg),
                    "qty": self.map2odoo_qty(qtyseg),
                    # price without taxes
                    "price_unit": self.map2odoo_unit_price(priseg),
                }
            )

        return lines
