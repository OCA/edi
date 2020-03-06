# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        vals = super(SaleOrderLine, self)._prepare_procurement_values(group_id=group_id)
        vals['edi_conversation_id'] = self.order_id.edi_conversation_id
        return vals


class StockRule(models.Model):
    """ A rule describe what a procurement should do; produce, buy, move, ... """
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields.append('edi_conversation_id')
        return fields


class StockMove(models.Model):
    _inherit = "stock.move"

    edi_conversation_id = fields.Char(string="EDI Conversation Id", copy=False)

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        vals['edi_conversation_id'] = self.edi_conversation_id
        return vals
