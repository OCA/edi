# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    adjustment_credit_account_id = fields.Many2one(
        'account.account', string='Adjustment Credit Account',
        domain=[('deprecated', '=', False)])
    adjustment_debit_account_id = fields.Many2one(
        'account.account', string='Adjustment Debit Account',
        domain=[('deprecated', '=', False)])
