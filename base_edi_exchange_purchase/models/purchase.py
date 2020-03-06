# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from lxml import etree
import logging
import uuid

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    @api.depends('transfer_ids')
    def _get_transfer_count(self):
        for record in self:
            record.transfer_count = len(record.transfer_ids.ids)

    partner_edi_exchange = fields.Boolean(string="Partner EDI Exchange Available", related="partner_id.edi_exchange_available")
    transfer_ids = fields.One2many('base.edi.transfer', 'po_id', string="Transfers")
    transfer_count = fields.Integer(string="Transfer Count", compute=_get_transfer_count, store=True)
    edi_conversation_id = fields.Char(string="EDI Conversation Id", copy=False)

    @api.model
    def _prepare_picking(self):
        vals = super(PurchaseOrder, self)._prepare_picking()
        vals['edi_conversation_id'] = self.edi_conversation_id
        return vals

    @api.multi
    def get_edi_send_values(self):
        self.ensure_one()
        return {
            'ref': 'purchase.order,%d' % self.id,
            'po_id': self.id,
            'conversation_id': self.edi_conversation_id,
        }

    @api.multi
    def send_via_edi_exchange(self):
        self.ensure_one()
        if not self.edi_conversation_id:
            self.edi_conversation_id = uuid.uuid4()
        if self.state in ('draft', 'sent'):
            result, mime = self.env.ref('purchase.report_purchase_quotation').render_qweb_pdf([self.id])
        else:
            result, mime = self.env.ref('purchase.action_report_purchase_order').render_qweb_pdf([self.id])
        try:
            vals = self.get_edi_send_values()
            for exchange in self.partner_id.available_exchange_ids:
                if exchange.send(result, vals):
                    break
        except Exception as e:
            _logger.error("Failure to send purchase.order with id %s on all channels! Please contact your system administrator.")
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
            'domain': "[('po_id', '=', %s)]" % self.id,
            'target': 'self',
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _prepare_stock_moves(self, picking):
        vals = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        for i in range(0, len(vals)):
            vals[i]['edi_conversation_id'] = picking.edi_conversation_id
        return vals