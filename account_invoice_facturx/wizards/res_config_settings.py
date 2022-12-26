# Copyright 2017-2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    facturx_level = fields.Selection(related="company_id.facturx_level", readonly=False)
    facturx_refund_type = fields.Selection(
        related="company_id.facturx_refund_type", readonly=False
    )
