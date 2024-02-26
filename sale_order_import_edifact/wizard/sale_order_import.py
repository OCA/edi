import json
import logging
import os
from base64 import b64decode
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class SaleOrderImport(models.TransientModel):
    _inherit = "sale.order.import"

    import_type = fields.Selection(
        selection_add=[("edifact", "EDIFACT")], ondelete={"edifact": "cascade"}
    )
    # Make doc_type field support for EDIFACT type
    doc_type = fields.Selection(readonly=False)
    # TODO: Move this feature to the base module or to an additional module.
    json_data_preview = fields.Text(
        help="Used by the btn `button_parse_order_preview` to preview data before importing"
    )
    edifact_ok = fields.Boolean(compute="_compute_edifact_ok")
    # Techincal fields used to get the extension part of files
    file_ext = fields.Char(default="txt,d96a")
    # EDIFACT format release
    release = fields.Char(default="d96a")

    @api.depends("order_file", "order_filename")
    def _compute_edifact_ok(self):
        for rec in self:
            if not (rec.order_file and rec.order_filename):
                rec.edifact_ok = False
                continue
            extensions = rec.file_ext.split(",")
            path, ext = os.path.splitext(self.order_filename)
            ok = ext and ext[1:] in extensions
            if not ok:
                ok = b64decode(self.order_file[:4]) in (b"UNA", b"UNB")
            rec.edifact_ok = ok

    # TODO: Move this feature to the base module or to an additional module.
    def button_parse_order_preview(self):
        """
        Generate a preview of the data before importing.

        This method is called by the button to take a quick look at the pydifact
        structure ('edifact' type) and the parsed object ('order') from
        the original document before importing the document.
        """

        self.ensure_one()
        edifact_model = self.env["base.edifact"]
        order_file_decoded = b64decode(self.order_file)
        parsed_obj = dict(edifact=None, order=None)
        if self.edifact_ok:
            parsed_obj["edifact"] = edifact_model.pydifact_obj(order_file_decoded)

        parsed_order = self.parse_order(
            order_file_decoded, self.order_filename, self.partner_id
        )
        del parsed_order["attachments"]
        parsed_obj["order"] = parsed_order
        self.write(
            {
                "json_data_preview": json.dumps(parsed_obj, indent=4, default=str),
            }
        )
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "sale_order_import.sale_order_import_action"
        )
        action["res_id"] = self.id
        return action

    def _get_supported_types(self):
        # Add more types for EDIFACT
        res = super()._get_supported_types()
        res.update({"edifact": ("text/plain", None)})
        return res

    @api.model
    def parse_edifact_order(self, filecontent, detect_doc_type=False):
        # https://github.com/nerdocs/pydifact/blob/master/pydifact/segmentcollection.py
        if detect_doc_type:
            if not self.edifact_ok:
                return None
            return self.env.context.get("default_doc_type", "rfq")

        edifact_model = self.env["base.edifact"]
        interchange = edifact_model._loads_edifact(filecontent)
        header = interchange.get_header_segment()
        # > UNB segment: [['UNOA', '2'], ['5450534000000', '14'],
        # ['8435337000003', '14'], ['230306', '0435'], '5506']

        msg_type, msg_type_release = edifact_model._get_msg_type(interchange)
        supported = ["ORDERS"]
        if msg_type not in supported:
            raise UserError(_("%s document is not a Sale Order document"))

        bgm = interchange.get_segment("BGM")
        # Customer PO number
        # BGM segment: ['220', '1LP6WZGF', '9']
        order_ref = bgm[1]

        rd = {
            "doc_type": self.doc_type,
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
            }
            if references.get("vat"):
                partner_dict["edi_ctx"]["rff_va"] = references["vat"]
        if parties.get("company"):
            parties["company"]["edi_ctx"]["vendor_code"] = references.get("vendor_code")
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
                # Delivery date
                dates["delivery_detail"][
                    "commitment_date"
                ] = edifact_model.map2odoo_date(seg[0])

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
            usage_code = seg[0]
            if usage_code == "2":
                currencies["currency"] = edifact_model.map2odoo_currency(seg)
        return currencies

    @api.model
    def _prepare_edifact_lines(self, interchange):
        edifact_model = self.env["base.edifact"]
        lines = []
        pia_list = []
        qty_list = []
        pri_list = []
        imd_list = []

        for i in interchange.get_segments("PIA"):
            if i[1][1] == "SA":
                pia_list.append(i)
        for i in interchange.get_segments("QTY"):
            if i[0][0] == "21":
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

            price_unit = edifact_model.map2odoo_unit_price(priseg)
            # If the product price is not provided, the price will be taken from the system
            if price_unit != 0.0:
                line["price_unit"] = price_unit
            description = edifact_model.map2odoo_description(imdseg)
            if description:
                line["name"] = description

            lines.append(line)

        return lines
