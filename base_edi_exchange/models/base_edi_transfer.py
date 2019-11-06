# -*- coding: utf-8 -*-
# Copyright 2019 Callino <wpichler@callino.at
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class BaseEDITransfer(models.Model):
    _name = 'base.edi.transfer'
    _description = 'Model to Track EDI Transfers'

    name = fields.Char(string="Name")
    original_filename = fields.Char(string="Original Filename")
    file_content = fields.Binary(string="File Content")
    state = fields.Selection(selection=[
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('accepted', _('Accepted')),
        ('processed', _('Processed')),
        ('error', _('Error')),
        ('manual', _('Manual'))
    ], string="State", default="pending")
    error_text = fields.Text(string="Error")
    ref = fields.Reference(string="Reference", selection=[])
    edi_exchange_id = fields.Many2one('base.edi.exchange', string="EDI Exchange", required=True, readonly=True)
    conversation_id = fields.Char('Conversation Id', index=True)
    message_id = fields.Char(string="Sent Filename", index=True)
    direction = fields.Selection(selection=[('inbound', _('Inbound')), ('outbound', _('Outbound'))], required=True)
    read_date = fields.Datetime(string="File read at")
    sent_date = fields.Datetime(string="File sent at")
    process_date = fields.Datetime(string="File processed at")
    file_timestamp = fields.Datetime(string="File last modified")

    _sql_constraints = [(
        'message_id_exchange_id_unique',
        'unique(message_id, edi_exchange_id)',
        'MessageId must be unique per exchange'
    )]

    @api.model
    def get_transfer(self, file):
        # search for transfer via filename
        transfer = self.search([('original_filename', '=', file)], limit=1)
        if not transfer:
            # no file with the same filename - might still be imported under different name
            return False
        else:
            return transfer

    @api.multi
    def identify_and_import_object(self):
        # Base function - has to get overwritten by exchange specific function
        self.state = "error"
        self.error_text = "File could not be identified."
        return False

    @api.multi
    def identify_and_update_object(self):
        # Base function - has to get overwritten by exchange specific function
        self.state = "error"
        self.error_text = "File could not be identified."
        return False
