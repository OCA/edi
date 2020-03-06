# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
import logging
import os
import base64
from odoo.addons.base_business_document_import.exceptions import WrongTypeError
import traceback, sys

_logger = logging.getLogger(__name__)


class BaseEDITransfer (models.Model):
    _inherit = 'base.edi.transfer'

    ref = fields.Reference(selection_add=[('sale.order', _('Sale'))])
    so_id = fields.Many2one('sale.order', string="Sale Order")

    @api.multi
    def identify_and_import_object(self):
        if self.conversation_id:
            # We got a conversation_id - search for existing sale order
            order = self.env['sale.order'].search([('edi_conversation_id', '=', self.conversation_id)], limit=1)
            if order:
                # This sale order does already exists - so this is an update !
                # Do set reference
                self.so_id = order.id
                self.ref = "sale.order,%d" % order.id
                # and start update
                res = self.identify_and_update_object()
                # If this update call did not generated an exception - then we can set the state to be processed
                self.state = 'processed'
                return res
        try:
            so_import = self.env['sale.order.import'].create({
                'order_file': base64.b64encode(self.file_content),
                'order_filename': self.original_filename,
                'state': 'import',
                'edi_conversation_id': self.conversation_id,
                'edi_transfer_id': self.id
            })
            order_dict = so_import.import_order_button()
            if order_dict['res_model'] == 'sale.order':
                order = self.env['sale.order'].browse(order_dict['res_id'])
                order.edi_conversation_id = self.conversation_id
                self.ref = 'sale.order,%d' % order_dict['res_id']
                self.so_id = order_dict['res_id']
                self.state = "processed"
                self.process_date = datetime.now()
                return order_dict
            else:
                _logger.info("Object Import reported as success - but no valid sale data.")
                self.state = "manual"
                return order_dict
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
            so_import = self.env['sale.order.import'].create({
                'order_file': base64.b64encode(self.file_content),
                'order_filename': self.original_filename,
                'state': 'import',
                'sale_id': self.ref.id,
            })
            action = so_import.update_order_button()
            if action['res_model'] == 'sale.order':
                self.ref = 'sale.order,%d' % action['res_id']
                self.state = "processed"
                self.process_date = datetime.now()
                return action
            else:
                _logger.info("Object Import reported as success - but no valid sale data.")
                self.state = "manual"
                return action
        except WrongTypeError as wte:
            return super(BaseEDITransfer, self).identify_and_import_object()
        except UserError as ue:
            self.state = 'error'
            self.error_text = str(ue)
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            self.state = 'error'
            self.error_text = str(e)

