# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountInvoiceImportPartnerCreate(models.TransientModel):
    _name = "account.invoice.import.partner.create"
    _description = "Wizard to create a new partner or update an existing partner"

    move_id = fields.Many2one(
        "account.move", readonly=True, required=True, string="Vendor Bill"
    )
    import_partner_data = fields.Json()
    create_or_update = fields.Selection(
        [
            ("create", "This partner doesn't already exists in Odoo"),
            ("update", "This partner already exists in Odoo"),
        ],
        required=True,
        default="create",
    )
    update_partner_id = fields.Many2one(
        "res.partner",
        domain=[("parent_id", "=", False)],
        string="Partner to Update",
    )
    partner_vat = fields.Char(string="Partner VAT Number", readonly=True)
    partner_name = fields.Char(readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get("active_model") == "account.move" and self._context.get(
            "active_id"
        ):
            res["move_id"] = self._context["active_id"]
            move = self.env["account.move"].browse(res["move_id"])
            import_partner_data = move.import_partner_data
            assert import_partner_data
            res["import_partner_data"] = import_partner_data
            if import_partner_data.get("vat"):
                res["partner_vat"] = import_partner_data["vat"]
            if import_partner_data.get("name"):
                res["partner_name"] = import_partner_data["name"]
            # Partner may have been created in the meantime
            res["update_partner_id"] = self.env[
                "business.document.import"
            ]._match_partner(import_partner_data, [], raise_exception=False)
        return res

    def create_partner(self):
        self.ensure_one()
        assert isinstance(self.import_partner_data, dict)
        assert self.move_id
        assert self.create_or_update == "create"
        ctx = {
            f"default_{key}": value for key, value in self.import_partner_data.items()
        }
        ctx["default_invoice_import_move_id"] = self.move_id.id
        action = {
            "type": "ir.actions.act_window",
            "name": _("Create New Partner"),
            "res_model": "res.partner",
            "view_mode": "form",
            "context": ctx,
        }
        return action

    def update_partner(self):
        self.ensure_one()
        assert self.create_or_update == "update"
        if not self.update_partner_id:
            raise UserError(_("You must select the partner to update."))
        self.update_partner_id._invoice_import_update_partner(self.import_partner_data)
        self.move_id._invoice_import_set_partner_and_update_lines(
            self.update_partner_id
        )
        self.move_id.message_post(
            body=_(
                "Partner <a href=# data-oe-model=res.partner "
                "data-oe-id=%(partner_id)s>%(partner_name)s</a> has been "
                "set via the wizard <em>Create or Update Partner</em>. "
                "The partner has been updated.",
                partner_id=self.update_partner_id.id,
                partner_name=self.update_partner_id.display_name,
            )
        )
