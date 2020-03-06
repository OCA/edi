# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import logging
import os
import glob
import lxml.etree as ET
import uuid
import os.path

_logger = logging.getLogger(__name__)

NSMAP = {
    "eb3": "http://docs.oasis-open.org/ebxml-msg/ebms/v3.0/ns/core/200704/",
    "mmd": "http://holodeck-b2b.org/schemas/2014/06/mmd"
}

def _get_as4_message_id(xml_content):
    # Do search for messageid in Holodeck namespace
    MessageId = xml_content.find('//mmd:MessageInfo/mmd:MessageId', namespaces=NSMAP)
    if MessageId is None:
        # If not found - then search for it in eb3 namespace
        MessageId = xml_content.find('//eb3:MessageInfo/eb3:MessageId', namespaces=NSMAP)
    if isinstance(MessageId, ET._Element) and MessageId.text:
        return MessageId.text
    else:
        return None


def _is_as4_signal_message(xml_content):
    return xml_content.find('//eb3:SignalMessage', namespaces=NSMAP) is not None


class BaseEDIExchange(models.Model):
    _inherit = 'base.edi.exchange'

    type = fields.Selection(selection_add=[('holodeck', _('Holodeck'))])

    send_folder = fields.Char(string="Folder to Send")
    receive_folder = fields.Char(string="Folder to Receive")
    archive_folder = fields.Char(string="Folder to Archive Received files")
    send_pmode = fields.Char(string="Pmode used for sending")
    receive_pmode = fields.Char(string="Pmode used for receiving")

    @api.multi
    def send(self, file, vals=None):
        if not vals:
            vals = {}
        _logger.debug('Base Send holodeck called.')
        if self.type != 'holodeck':
            return super(BaseEDIExchange, self).send()
        message_id = uuid.uuid4()
        vals.update({
            'name': message_id,
            'message_id': message_id,
            'original_filename': "%s.mmd" % message_id,
            'file_content': file,
            'state': 'pending',
            'edi_exchange_id': self.id,
            'direction': 'outbound',
        })
        file_transfer = self.env['base.edi.transfer'].create(vals)
        file_transfer.send_object()
        return True

    @api.multi
    def receive(self):
        self.ensure_one()
        _logger.debug('Base Receive Holodeck called.')
        if self.type != 'holodeck':
            return super(BaseEDIExchange, self).receive()
        self.check_sent_state()
        self.check_received_files()

    @api.multi
    def check_sent_state(self):
        transfers = self.env['base.edi.transfer'].search([('edi_exchange_id', '=', self.id), ('state', '=', 'sent')])
        for transfer in transfers:
            if os.path.isfile(os.path.join(self.send_folder, "%s.accepted" % transfer.message_id)):
                transfer.state = 'accepted'
            if os.path.isfile(os.path.join(self.send_folder, "%s.err" % transfer.message_id)):
                transfer.state = 'error'

    @api.multi
    def process_ref_to_message(self, xml_content):
        self.ensure_one()
        RefToMessageId = xml_content.find('//eb3:SignalMessage/eb3:MessageInfo/eb3:RefToMessageId', namespaces=NSMAP)
        transfer = self.env['base.edi.transfer'].search([
            ('message_id', '=', RefToMessageId.text),
            ('edi_exchange_id', '=', self.id)
        ])
        if not transfer:
            raise Exception(_('We received a unknown message response'))
        Receipt = xml_content.find('//eb3:SignalMessage/eb3:Receipt', namespaces=NSMAP)
        if Receipt is not None:
            transfer.state = 'processed'
        Error = xml_content.find('//eb3:SignalMessage/eb3:Error', namespaces=NSMAP)
        if Error is not None:
            transfer.state = 'error'
            # TODO: Add error message from xml to transfer
        return transfer

    @api.multi
    def check_received_files(self):
        files = glob.glob(os.path.join(self.receive_folder, "*.xml"))
        for complete_path in files:
            file = os.path.basename(complete_path)
            try:
                with open(complete_path, 'rb') as xml_file:
                    xml_content = ET.parse(xml_file)
                # Read MessageId - if MessageId is missing - then it is no AS4 Message !!!
                MessageId = _get_as4_message_id(xml_content)
                if not MessageId:
                    # Move file into error folder
                    error_folder = os.path.join(self.receive_folder, "error")
                    os.rename(complete_path, os.path.join(error_folder, file))
                    continue
                # Check for Signal Messages
                if _is_as4_signal_message(xml_content):
                    transfer = self.process_ref_to_message(xml_content)
                    # If this worked without exception - then we move the file to the archive folder

                    os.rename(complete_path, os.path.join(transfer.confirmation_folder, file))
                    continue
                # If it is no Signal Message - then it must have a PartInfo with location to payload
                file_attachment_location = xml_content.find(
                    './/{http://holodeck-b2b.org/schemas/2014/06/mmd}PartInfo').get("location")
            except Exception as e:
                # Move file into error folder
                error_folder = os.path.join(self.receive_folder, "error")
                os.rename(complete_path, os.path.join(error_folder, file))
                continue
            # check if file was read and processed before
            file_transfer = self.env['base.edi.transfer'].search([('message_id', '=', MessageId)])
            if file_transfer:
                # This should not happen - we move it into error folder
                error_folder = os.path.join(self.receive_folder, "error")
                os.rename(complete_path, os.path.join(error_folder, file))
                os.rename(file_attachment_location,
                          os.path.join(error_folder, os.path.basename(file_attachment_location)))
                continue
            # no file transfer - create new one
            ConversationId = xml_content.find(
                './{http://holodeck-b2b.org/schemas/2014/06/mmd}CollaborationInfo/{http://holodeck-b2b.org/schemas/2014/06/mmd}ConversationId')
            with open(file_attachment_location, 'rb') as file_to_process:
                file_content = file_to_process.read()
                transfer_vals = {
                    'name': file,
                    'original_filename': "%s.pdf" % file_attachment_location,
                    'file_content': file_content,
                    'state': 'pending',
                    'edi_exchange_id': self.id,
                    'conversation_id': ConversationId.text,
                    'message_id': MessageId,
                    'direction': 'inbound',
                    'file_timestamp': datetime.utcfromtimestamp(os.path.getmtime(file_attachment_location)),
                    'read_date': datetime.now(),
                }
            file_transfer = self.env['base.edi.transfer'].create(transfer_vals)
            try:
                file_transfer.identify_and_import_object()
                _logger.info("Move %s to %s", complete_path, os.path.join(file_transfer.inbound_archive_folder, file))
                os.rename(complete_path, os.path.join(file_transfer.inbound_archive_folder, file))
                _logger.info("Move %s to %s", file_attachment_location,
                             os.path.join(file_transfer.inbound_attachment_archive_folder,
                                          os.path.basename(file_attachment_location)))
                os.rename(file_attachment_location, os.path.join(file_transfer.inbound_attachment_archive_folder,
                                                                 os.path.basename(file_attachment_location)))
            except Exception as e:
                continue
        return True

    @api.multi
    def create_send_xml(self, path, transfer):
        root = ET.Element("MessageMetaData")
        # CollarborationInfo
        colaboration_info = ET.SubElement(root, "CollaborationInfo")
        aggreement_ref = ET.SubElement(colaboration_info, "AgreementRef")
        aggreement_ref.set('pmode', self.send_pmode)
        conversation_id = ET.SubElement(colaboration_info, "ConversationId")
        conversation_id.text = transfer.conversation_id

        # MessageInfo
        message_info = ET.SubElement(root, "MessageInfo")
        message_id = ET.SubElement(message_info, "MessageId")
        message_id.text = transfer.message_id

        # Payload Info
        payload_info = ET.SubElement(root, "PayloadInfo")
        part_info = ET.SubElement(payload_info, "PartInfo")
        part_info.set('containment', "attachment")
        part_info.set('mimeType', "text/pdf")
        part_info.set('location', path)

        tree = ET.ElementTree(root)
        tree.write(os.path.join(self.send_folder, "%s.mmd" % transfer.message_id))
