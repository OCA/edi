# -*- coding: utf-8 -*-
# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrderImport(models.TransientModel):
    _inherit = 'purchase.order.import'

    @api.model
    def _get_purchase_id(self):
        if self._context.get('is_automatic', False):
            return
        assert self._context['active_model'] == 'purchase.order',\
            'bad active_model'
        return self.env['purchase.order'].browse(self._context['active_id'])#

    purchase_id = fields.Many2one(
        'purchase.order', string='RFQ to Update', default=_get_purchase_id,
        readonly=True)