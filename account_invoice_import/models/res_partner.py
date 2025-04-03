# Copyright 2015-2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # DEFAULT VALUE fields
    invoice_import_product_id = fields.Many2one(
        "product.product", string="Default Product", company_dependent=True
    )
    # only if invoice_import_product_id is not set
    invoice_import_account_id = fields.Many2one(
        "account.account",
        company_dependent=True,
        string="Default Expense Account",
        domain="[('deprecated', '=', False), ('company_id', '=', current_company_id)]",
        help="The account configured here will go through the mapping of the fiscal position.",
    )
    # only if invoice_import_product_id is not set
    invoice_import_tax_ids = fields.Many2many(
        "account.tax",
        string="Default Taxes",
        domain="[('type_tax_use', '=', 'purchase'), ('company_id', '=', current_company_id)]",
        help="Taxes configured here will go through the mapping of the fiscal position.",
    )
    # FORCE VALUE fields
    # company_dependent=True ??
    invoice_import_single_line = fields.Boolean(string="Force Single Invoice Line")
    invoice_import_label = fields.Char(
        string="Force Invoice Line Description", help="Force Invoice Line Description"
    )

    invoice_import_journal_id = fields.Many2one(
        "account.journal",
        string="Force Purchase Journal",
        company_dependent=True,
        domain="[('type', '=', 'purchase'), ('company_id', '=', current_company_id)]",
        help="If empty, Odoo will use the first purchase journal.",
    )
    # For analytic, users should use the ability to auto-set an analytic distribution
    # depending on product/partner

    def _convert_to_import_config(self, company):
        self.ensure_one()
        if not company:
            company = self.env.company
        self = self.with_company(company.id)
        vals = {
            "company": company,
            "single_line": self.invoice_import_single_line,
            "label": self.invoice_import_label or False,
            "journal": self.invoice_import_journal_id or False,
        }
        if self.invoice_import_product_id:
            vals["product"] = self.invoice_import_product_id
        else:
            taxes = (
                self.invoice_import_tax_ids
                and self.invoice_import_tax_ids.filtered(
                    lambda tax: tax.company_id == company
                )
                or False
            )
            if taxes:
                vals["taxes"] = taxes
            if (
                self.invoice_import_account_id
                and self.invoice_import_account_id.company_id == company
            ):
                vals["account"] = self.invoice_import_account_id
        return vals
