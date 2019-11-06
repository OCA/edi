# -*- coding: utf-8 -*-
# Copyright 2019 Callino <wpichler@callino.at
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class BaseEDIExchange(models.Model):
    _name = 'base.edi.exchange'
    _description = 'Common methods to send and receive EDI files'

    @api.multi
    @api.depends('transfer_ids')
    def _get_transfer_counts(self):
        for record in self:
            record.pending_transfer_count = len(record.transfer_ids.filtered(lambda r: r.state == 'pending'))
            record.sent_transfer_count = len(record.transfer_ids.filtered(lambda r: r.state == 'sent'))
            record.processed_transfer_count = len(record.transfer_ids.filtered(lambda r: r.state == 'processed'))
            record.error_transfer_count = len(record.transfer_ids.filtered(lambda r: r.state == 'error'))
            record.manual_transfer_count = len(record.transfer_ids.filtered(lambda r: r.state == 'manual'))

    name = fields.Char(string="Name")
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(selection=[('disabled', 'Disabled'), ('enabled', 'Enabled')], string="State",
                             default='disabled')
    type = fields.Selection(selection=[('none', _('None'))], string="Type", required=True)
    interval = fields.Integer(string="Interval (min)", default=15)
    last_run = fields.Datetime(string="Last Run", readonly=True)
    transfer_ids = fields.One2many('base.edi.transfer', 'edi_exchange_id', string="Transfers Inbound")
    inbound_transfer_ids = fields.One2many('base.edi.transfer', 'edi_exchange_id', string="Transfers Inbound",
                                           domain=[('direction', '=', 'inbound')], readonly=True)
    outbound_transfer_ids = fields.One2many('base.edi.transfer', 'edi_exchange_id', string="Transfers Outbound",
                                            domain=[('direction', '=', 'outbound')], readonly=True)
    partner_ids = fields.Many2many('res.partner', string="Partners")
    pending_transfer_count = fields.Integer(string="Pending Transfers", compute=_get_transfer_counts)
    sent_transfer_count = fields.Integer(string="Sent Transfers", compute=_get_transfer_counts)
    processed_transfer_count = fields.Integer(string="Processed Transfers", compute=_get_transfer_counts)
    error_transfer_count = fields.Integer(string="Error Transfers", compute=_get_transfer_counts)
    manual_transfer_count = fields.Integer(string="Manual Transfers", compute=_get_transfer_counts)

    @api.multi
    def send(self, file, vals=None):
        pass

    @api.multi
    def receive(self):
        pass

    @api.model
    def check_active_exchanges(self):
        """
        Will get called from cronjob to call the receive function of all active exchanges
        The time interval for each exchange can get set
        :return:
        """
        for exchange in self.env['base.edi.exchange'].search([('state', '=', 'enabled')]):
            if not exchange.last_run or datetime.now() > (exchange.last_run + timedelta(minutes=exchange.interval)):
                exchange.receive()
                exchange.last_run = datetime.now()

    @api.multi
    def action_pending_transfers(self):
        self.ensure_one()
        return {
            'name': _("Pending Transfers"),
            'type': 'ir.actions.act_window',
            'res_model': 'base.edi.transfer',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': "[('state', '=', 'pending'), ('edi_exchange_id', '=', %s)]" % self.id,
            'target': 'self',
        }

    @api.multi
    def action_sent_transfers(self):
        self.ensure_one()
        return {
            'name': _("Sent Transfers"),
            'type': 'ir.actions.act_window',
            'res_model': 'base.edi.transfer',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': "[('state', '=', 'sent'), ('edi_exchange_id', '=', %s)]" % self.id,
            'target': 'self',
        }

    @api.multi
    def action_processed_transfers(self):
        self.ensure_one()
        return {
            'name': _("Processed Transfers"),
            'type': 'ir.actions.act_window',
            'res_model': 'base.edi.transfer',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': "[('state', '=', 'processed'), ('edi_exchange_id', '=', %s)]" % self.id,
            'target': 'self',
        }

    @api.multi
    def action_error_transfers(self):
        self.ensure_one()
        return {
            'name': _("Error Transfers"),
            'type': 'ir.actions.act_window',
            'res_model': 'base.edi.transfer',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': "[('state', '=', 'error'), ('edi_exchange_id', '=', %s)]" % self.id,
            'target': 'self',
        }

    @api.multi
    def action_manual_transfers(self):
        self.ensure_one()
        return {
            'name': _("Manual Transfers"),
            'type': 'ir.actions.act_window',
            'res_model': 'base.edi.transfer',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': "[('state', '=', 'manual'), ('edi_exchange_id', '=', %s)]" % self.id,
            'target': 'self',
        }
