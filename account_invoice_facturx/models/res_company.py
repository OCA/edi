# Copyright 2017-2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import fields, models, tools


class ResCompany(models.Model):
    _inherit = "res.company"

    xml_format_in_pdf_invoice = fields.Selection(
        selection_add=[("factur-x", "Factur-X (CII)")],
        default="factur-x",
        ondelete={"factur-x": "set null"},
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
    )
    # up to v15, this module inherited the invoice report to add the
    # facturx logo. In v16, I decided to stop inheriting the invoice report
    # because I think many users may not want to have the facturx logo,
    # but I continue to provide the field 'facturx_logo'

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
