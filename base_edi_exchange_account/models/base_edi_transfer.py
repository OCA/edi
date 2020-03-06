# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
import logging
import os
import base64
from odoo.addons.base_business_document_import.exceptions import WrongTypeError

_logger = logging.getLogger(__name__)


class BaseEDITransfer (models.Model):
    _inherit = 'base.edi.transfer'

    ref = fields.Reference(selection_add=[('account.invoice', _('Invoice'))])
    ai_id = fields.Many2one('account.invoice', string="Invoice")

    @api.multi
    def identify_and_import_object(self):
        try:
            ai_import = self.env['account.invoice.import'].create({
                'invoice_file': base64.b64encode(self.file_content),
                'invoice_filename': self.original_filename,
                'state': 'import'
            })
            invoice_dict = ai_import.import_invoice()
            if invoice_dict['res_model'] == 'account.invoice':
                invoice = self.env['account.invoice'].browse(invoice_dict['res_id'])
                invoice.edi_conversation_id = self.conversation_id
                self.ref = 'account.invoice,%d' % invoice_dict['res_id']
                self.ai_id = invoice_dict['res_id']
                self.state = "processed"
                self.process_date = datetime.now()
                return invoice_dict
            else:
                _logger.info("Object Import reported as success - but no valid sale data.")
                self.state = "manual"
                return invoice_dict
        except WrongTypeError as wte:
            return super(BaseEDITransfer, self).identify_and_import_object()
        except UserError as ue:
            self.state = 'error'
            self.error_text = str(ue)
        except Exception as e:
            self.state = 'error'
            self.error_text = str(e)

    @api.multi
    def identify_and_update_object(self):
        try:
            ai_import = self.env['account.invoice.import'].create({
                'invoice_file': base64.b64encode(self.file_content),
                'invoice_filename': self.original_filename,
                'state': 'import'
            })
            invoice = ai_import.update_invoice()
            # TODO: Check this if correct on update
            invoice.edi_conversation_id = self.conversation_id
            if invoice['res_model'] == 'account.invoice':
                self.ref = 'account.invoice,%d' % invoice['res_id']
                self.state = "processed"
                self.process_date = datetime.now()
                return invoice
            else:
                _logger.info("Object Import reported as success - but no valid sale data.")
                self.state = "manual"
                return invoice
        except Exception as e:
            return super(BaseEDITransfer, self).identify_and_import_object()

