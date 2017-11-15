# -*- coding: utf-8 -*-
# © 2017 Akretion - Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    facturx_level = fields.Selection(related='company_id.facturx_level')
    facturx_refund_type = fields.Selection(
        related='company_id.facturx_refund_type')
