# Copyright 2017-2020 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import fields, models, tools


class ResCompany(models.Model):
    _inherit = "res.company"

    xml_format_in_pdf_invoice = fields.Selection(
        selection_add=[("factur-x", "Factur-X (CII)")], default="factur-x"
    )
    facturx_level = fields.Selection(
        [
            ("minimum", "Minimum"),
            ("basicwl", "Basic without lines"),
            ("basic", "Basic"),
            ("en16931", "EN 16931 (Comfort)"),
            ("extended", "Extended"),
        ],
        string="Factur-X Level",
        default="en16931",
        help="Unless if you have a good reason, you should always "
        "select 'EN 16931 (Comfort)', which is the default value.",
    )
    facturx_refund_type = fields.Selection(
        [
            ("380", "Type 380 with negative amounts"),
            ("381", "Type 381 with positive amounts"),
        ],
        string="Factur-X Refund Type",
        default="381",
    )
    facturx_logo = fields.Binary(
        compute="_compute_facturx_logo",
        string="Factur-X Logo",
        help="Logo to include in the visible part of Factur-X invoices",
        readonly=True,
    )

    def _compute_facturx_logo(self):
        level2logo = {
            "minimum": "factur-x-minimum.png",
            "basicwl": "factur-x-basicwl.png",
            "basic": "factur-x-basic.png",
            "en16931": "factur-x-en16931.png",
            "extended": "factur-x-extended.png",
        }
        for company in self:
            facturx_logo = False
            if (
                company.xml_format_in_pdf_invoice == "factur-x"
                and company.facturx_level
                and company.facturx_level in level2logo
            ):
                fname = level2logo[company.facturx_level]
                fname_path = "account_invoice_facturx/static/logos/%s" % fname
                f = tools.file_open(fname_path, "rb")
                f_binary = f.read()
                if f_binary:
                    facturx_logo = base64.b64encode(f_binary)

            company.facturx_logo = facturx_logo

    # Code in account_tax_unece in v14.0
    def _get_tax_unece_speeddict(self):
        self.ensure_one()
        res = {}
        tax_obj = self.env["account.tax"]
        all_taxes = tax_obj.with_context(active_test=False).search_read(
            [("company_id", "=", self.id)],
            [
                "unece_type_code",
                "unece_categ_code",
                "unece_due_date_code",
                "amount",
                "amount_type",
                "name",
                "display_name",
            ],
        )
        for tax in all_taxes:
            res[tax["id"]] = {
                "unece_type_code": tax["unece_type_code"] or None,
                "unece_categ_code": tax["unece_categ_code"] or None,
                "unece_due_date_code": tax["unece_due_date_code"] or None,
                "amount_type": tax["amount_type"],
                "amount": tax["amount"],
                "name": tax["name"],
                "display_name": tax["display_name"],
            }
        return res

    # Code in account_tax_unece in v14.0
    def _get_fiscal_position_speeddict(self, lang):
        self.ensure_one()
        res = {}
        fp_obj = self.env["account.fiscal.position"]
        fpositions = fp_obj.with_context(lang=lang, active_test=False).search_read(
            [("company_id", "=", self.id)], ["name", "display_name", "note"]
        )
        for fp in fpositions:
            res[fp["id"]] = {
                "name": fp["name"],
                "display_name": fp["display_name"],
                "note": fp["note"],  # supposed to store the exemption reason
            }
        return res
