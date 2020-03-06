# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
import logging
import os

_logger = logging.getLogger(__name__)


class BaseEDITransfer (models.Model):
    _inherit = 'base.edi.transfer'

    @api.depends('conversation_id', 'edi_exchange_id')
    def _compute_archive_folders(self):
        for transfer in self:
            conversation_folder = os.path.join(transfer.edi_exchange_id.archive_folder, transfer.conversation_id)
            transfer.conversation_folder = conversation_folder
            transfer.confirmation_folder = os.path.join(conversation_folder, "confirmation")
            transfer.inbound_archive_folder = os.path.join(conversation_folder, "inbound")
            transfer.outbound_archive_folder = os.path.join(conversation_folder, "outbound")
            transfer.outbound_attachment_archive_folder = os.path.join(conversation_folder, "outbound/attachments")
            transfer.inbound_attachment_archive_folder = os.path.join(conversation_folder, "inbound/attachments")
            # TODO: Error handling when it is not possible to create folders !
            if not os.path.exists(conversation_folder):
                os.makedirs(conversation_folder)
            if not os.path.exists(transfer.confirmation_folder):
                os.makedirs(transfer.confirmation_folder)
            if not os.path.exists(transfer.inbound_archive_folder):
                os.makedirs(transfer.inbound_archive_folder)
            if not os.path.exists(transfer.outbound_archive_folder):
                os.makedirs(transfer.outbound_archive_folder)
            if not os.path.exists(transfer.outbound_attachment_archive_folder):
                os.makedirs(transfer.outbound_attachment_archive_folder)
            if not os.path.exists(transfer.inbound_attachment_archive_folder):
                os.makedirs(transfer.inbound_attachment_archive_folder)

    conversation_folder = fields.Char(string="Conversation Folder", compute="_compute_archive_folders")
    confirmation_folder = fields.Char(string="Confirmation Folder", compute="_compute_archive_folders")
    inbound_archive_folder = fields.Char(string="Inbound Folder", compute="_compute_archive_folders")
    inbound_attachment_archive_folder = fields.Char(string="Inbound Folder", compute="_compute_archive_folders")
    outbound_archive_folder = fields.Char(string="Outbound Folder", compute="_compute_archive_folders")
    outbound_attachment_archive_folder = fields.Char(string="Outbound Attachment Folder",
                                                     compute="_compute_archive_folders")

    @api.multi
    def send_object(self):
        attachment_path = os.path.join(self.edi_exchange_id.send_folder, "attachments", self.message_id)
        with open(attachment_path, 'wb+') as f:
            f.write(self.file_content)
        self.edi_exchange_id.create_send_xml(attachment_path, self)
        self.state = 'sent'
        self.sent_date = datetime.now()
