# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    voxel_enabled = fields.Boolean(string="Enable Voxel")

    def _commercial_fields(self):
        return super()._commercial_fields() + ["voxel_enabled"]

    def _get_voxel_vat(self):
        """Rip initial ES prefix if exists."""
        self.ensure_one()
        vat = self.vat or ""
        if vat.startswith("ES"):
            return vat[2:]
        return vat
