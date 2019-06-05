# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    voxel_enabled = fields.Boolean(string='Enable Voxel')

    def _commercial_fields(self):
        return super(ResPartner, self)._commercial_fields() + ['voxel_enabled']
