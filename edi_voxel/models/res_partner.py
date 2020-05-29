# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    voxel_enabled = fields.Boolean(string="Enable Voxel")

    def _commercial_fields(self):
        return super(ResPartner, self)._commercial_fields() + ["voxel_enabled"]

    def _get_voxel_vat(self):
        """Rip initial ES prefix if exists."""
        self.ensure_one()
        if self.vat.startswith("ES"):
            return self.vat[2:]
        return self.vat
