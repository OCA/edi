# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.ondelete(at_uninstall=False)
    def _prevent_no_autocreate_partner_unlink(self):
        partner_not_found = self.env.ref(
            "account_edi_no_autocreate_partner.partner_not_found"
        )
        if partner_not_found in self:
            raise UserError(
                self.env._(
                    "You cannot delete the fallback 'Partner Not Found' contact "
                    "used for invoice imports."
                )
            )
        return super().unlink()

    def write(self, vals):
        if "active" in vals and vals["active"]:
            partner_not_found = self.env.ref(
                "account_edi_no_autocreate_partner.partner_not_found"
            )
            if partner_not_found in self:
                raise UserError(
                    self.env._(
                        "You cannot activate the fallback 'Partner Not Found' "
                        "contact used for invoice imports."
                    )
                )
        return super().write(vals)

    def _retrieve_partner(
        self, name=None, phone=None, email=None, vat=None, domain=None, company=None
    ):
        partner = super()._retrieve_partner(
            name=name, phone=phone, email=email, vat=vat, domain=domain, company=company
        )
        if not partner:
            partner = self.env.ref(
                "account_edi_no_autocreate_partner.partner_not_found"
            )
        return partner
