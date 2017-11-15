# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    facturx_level = fields.Selection([
        ('minimum', 'Minimum'),
        ('basicwl', 'Basic without lines'),
        ('basic', 'Basic'),
        ('en16931', 'EN 16931 (Comfort)'),
        ], string='Factur-X Level', default='en16931',
        help="Unless if you have a good reason, you should always "
        "select 'EN 16931 (Comfort)', which is the default value.")
    facturx_refund_type = fields.Selection([
        ('380', 'Type 380 with negative amounts'),
        ('381', 'Type 381 with positive amounts'),
        ], string='Factur-X Refund Type', default='381')
