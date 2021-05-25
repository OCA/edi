# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountInvoiceImportConfig(models.Model):
    _name = "account.invoice.import.config"
    _description = "Configuration for the import of Supplier Invoices"
    _order = "sequence"
    _check_company_auto = True

    name = fields.Char(required=True)
    partner_id = fields.Many2one(
        "res.partner",
        ondelete="cascade",
        domain=[("parent_id", "=", False)],
    )
    active = fields.Boolean(default=True)
    sequence = fields.Integer()
    invoice_line_method = fields.Selection(
        [
            ("1line_no_product", "Single Line, No Product"),
            ("1line_static_product", "Single Line, Static Product"),
            ("nline_no_product", "Multi Line, No Product"),
            ("nline_static_product", "Multi Line, Static Product"),
            ("nline_auto_product", "Multi Line, Auto-selected Product"),
        ],
        string="Method for Invoice Line",
        required=True,
        default="1line_no_product",
        help="The multi-line methods will not work for PDF invoices "
        "that don't have an embedded XML file which has structured information "
        "on each line.",
    )
    company_id = fields.Many2one(
        "res.company",
        ondelete="cascade",
        required=True,
        default=lambda self: self.env.company,
    )
    account_id = fields.Many2one(
        "account.account",
        string="Expense Account",
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
    )
    account_analytic_id = fields.Many2one(
        "account.analytic.account", string="Analytic Account", check_company=True
    )
    label = fields.Char(
        string="Force Description", help="Force supplier invoice line description"
    )
    tax_ids = fields.Many2many(
        "account.tax",
        string="Taxes",
        domain="[('type_tax_use', '=', 'purchase'), ('company_id', '=', company_id)]",
        check_company=True,
    )
    static_product_id = fields.Many2one(
        "product.product",
        check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )

    @api.constrains("invoice_line_method", "account_id", "static_product_id")
    def _check_import_config(self):
        for config in self:
            if (
                "static_product" in config.invoice_line_method
                and not config.static_product_id
            ):
                raise ValidationError(
                    _(
                        "Static Product must be set on the invoice import "
                        "configuration of supplier '%s' that has a Method "
                        "for Invoice Line set to 'Single Line, Static Product' "
                        "or 'Multi Line, Static Product'."
                    )
                    % config.partner_id.name
                )
            if "no_product" in config.invoice_line_method and not config.account_id:
                raise ValidationError(
                    _(
                        "The Expense Account must be set on the invoice "
                        "import configuration of supplier '%s' that has a "
                        "Method for Invoice Line set to 'Single Line, No Product' "
                        "or 'Multi Line, No Product'."
                    )
                    % config.partner_id.name
                )

    @api.onchange("invoice_line_method", "account_id")
    def invoice_line_method_change(self):
        if self.invoice_line_method == "1line_no_product" and self.account_id:
            self.tax_ids = [(6, 0, self.account_id.tax_ids.ids)]
        elif self.invoice_line_method != "1line_no_product":
            self.tax_ids = [(6, 0, [])]

    def convert_to_import_config(self):
        self.ensure_one()
        vals = {
            "invoice_line_method": self.invoice_line_method,
            "account_analytic": self.account_analytic_id or False,
        }
        if self.invoice_line_method == "1line_no_product":
            vals["account"] = self.account_id
            vals["taxes"] = self.tax_ids
            vals["label"] = self.label or False
        elif self.invoice_line_method == "1line_static_product":
            vals["product"] = self.static_product_id
            vals["label"] = self.label or False
        elif self.invoice_line_method == "nline_no_product":
            vals["account"] = self.account_id
        elif self.invoice_line_method == "nline_static_product":
            vals["product"] = self.static_product_id
        return vals
