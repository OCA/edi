# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    ubl_default_payment_mode = fields.Many2one(
        comodel_name="payment.mode",
        string="Use this payment mode as default if an invoice has none",
        help="Use this payment mode to fill out PaymentMeans")
