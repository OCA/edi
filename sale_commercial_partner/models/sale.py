# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# © 2017-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).).

from openerp import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commercial_partner_id = fields.Many2one(
        related='partner_id.commercial_partner_id', store=True,
        string='Commercial Customer')
