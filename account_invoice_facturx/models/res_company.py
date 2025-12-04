# Copyright 2017-2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, tools


class ResCompany(models.Model):
    _inherit = "res.company"

    xml_format_in_pdf_invoice = fields.Selection(
        selection_add=[("factur-x", "Factur-X (CII)")],
        default="factur-x",
        ondelete={"factur-x": "set null"},
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
        for company in self:
            facturx_logo = False
            if company.xml_format_in_pdf_invoice == "factur-x":
                fname = "factur-x-extended.png"
                fname_path = f"account_invoice_facturx/static/logos/{fname}"
                with tools.file_open(fname_path, "rb") as flogo:
                    facturx_logo = flogo.read()
            company.facturx_logo = facturx_logo
