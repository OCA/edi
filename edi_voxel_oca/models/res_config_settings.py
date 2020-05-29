# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    voxel_send_mode = fields.Selection(
        related="company_id.voxel_send_mode", readonly=False
    )
    voxel_sent_time = fields.Float(related="company_id.voxel_sent_time", readonly=False)
    voxel_delay_time = fields.Float(
        related="company_id.voxel_delay_time", readonly=False
    )
