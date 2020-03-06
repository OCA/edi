# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from lxml import etree
import logging
import uuid

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    @api.depends('transfer_ids')
    def _get_transfer_count(self):
        for record in self:
            record.transfer_count = len(record.transfer_ids.ids)

    partner_edi_exchange = fields.Boolean(string="Partner EDI Exchange Available",
                                          related="partner_id.edi_exchange_available")
    transfer_ids = fields.One2many('base.edi.transfer', 'picking_id', string="Transfers")
    transfer_count = fields.Integer(string="Transfer Count", compute=_get_transfer_count, store=True)
    edi_conversation_id = fields.Char(string="EDI Conversation Id", copy=False)

    @api.multi
    def get_edi_send_values(self):
        self.ensure_one()
        return {
            'ref': 'stock.picking,%d' % self.id,
            'picking_id': self.id,
            'conversation_id': self.edi_conversation_id,
        }

    @api.multi
    def send_via_edi_exchange(self):
        self.ensure_one()
        if not self.edi_conversation_id:
            self.edi_conversation_id = uuid.uuid4()
        result, mime = self.env.ref('stock.action_report_delivery').render_qweb_pdf([self.id])
        try:
            for exchange in self.partner_id.available_exchange_ids:
                vals = self.get_edi_send_values()
                if exchange.send(result, vals):
                    break
        except Exception as e:
            _logger.error(
                "Failure to send sale.order with id %s on all channels! Please contact your system administrator.")
        return

    @api.multi
    def add_edi_exchange_to_partner(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.partner_id.id,
            'target': 'current',
        }

    @api.multi
    def open_transfers(self):
        self.ensure_one()
        return {
            'name': _("Transfers"),
            'type': 'ir.actions.act_window',
            'res_model': 'base.edi.transfer',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': "[('so_id', '=', %s)]" % self.id,
            'target': 'self',
        }
