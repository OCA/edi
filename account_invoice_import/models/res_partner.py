# Copyright 2015-2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


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
        help="The account configured here will be updated by the mapping of the "
        "fiscal position.",
    )
    # only if invoice_import_product_id is not set
    invoice_import_tax_ids = fields.Many2many(
        "account.tax",
        string="Default Taxes",
        domain="[('type_tax_use', '=', 'purchase'), ('company_id', '=', current_company_id)]",
        help="Taxes configured here will go through the mapping of the fiscal position.",
    )
    # FORCE VALUE fields
    invoice_import_single_line = fields.Boolean(
        string="Force Single Invoice Line", company_dependent=True
    )
    invoice_import_label = fields.Char(
        string="Force Invoice Line Description",
        help="Force Invoice Line Description",
        company_dependent=True,
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
    # Technical field for the create partner scenario
    invoice_import_move_id = fields.Many2one(
        "account.move", string="Related Imported Vendor Bill", readonly=True
    )
    invoice_import_move_partner_id = fields.Many2one(
        related="invoice_import_move_id.partner_id"
    )

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

    def update_imported_invoice(self):
        """Method called by button in partner banner"""
        self.ensure_one()
        invoice_import_move = self.invoice_import_move_id
        assert invoice_import_move
        self.write({"invoice_import_move_id": False})
        self.message_post(
            body=_(
                "Partner created from imported vendor bill <a href=# data-oe-model=pos.order "
                "data-oe-id=%(move_id)d>%(move_name)s</a>",
                move_id=invoice_import_move.id,
                move_name=invoice_import_move.display_name,
            )
        )
        if invoice_import_move.partner_id:
            raise UserError(
                _(
                    "The vendor bill %(move)s already has a partner %(partner)s.",
                    move=invoice_import_move.display_name,
                    partner=invoice_import_move.partner_id.display_name,
                )
            )
        invoice_import_move._invoice_import_set_partner_and_update_lines(self)
        invoice_import_move.message_post(
            body=_(
                "The partner has been created via the <em>create or update partner</em> wizard."
            )
        )
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_in_invoice_type"
        )
        action.update(
            {
                "view_id": False,
                "views": False,
                "view_mode": "form,tree",
                "res_id": invoice_import_move.id,
            }
        )
        return action
