# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2025, 2024 Guavana - Leonardo J. Caballero G.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    voxel_invoice_login_id = fields.Many2one(
        related="company_id.voxel_invoice_login_id", readonly=False
    )
