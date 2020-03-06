# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
import logging
import os
import base64
from odoo.addons.base_business_document_import.exceptions import WrongTypeError
import sys, traceback

_logger = logging.getLogger(__name__)


class BaseEDITransfer (models.Model):
    _inherit = 'base.edi.transfer'

    ref = fields.Reference(selection_add=[('purchase.order', _('Purchase'))])
    po_id = fields.Many2one('purchase.order', string="Purchase Order")

    @api.multi
    def identify_and_import_object(self):
        try:
            po_import = self.env['purchase.order.import'].with_context({'is_automatic': True}).create({
                'quote_file': base64.b64encode(self.file_content),
                'quote_filename': self.original_filename,
            })
            po_import.purchase_id = self._try_match_po(po_import.parse_quote(self.file_content, self.original_filename))
            success = po_import.update_rfq_button()
            self.process_date = datetime.now()
            if success == True:
                po_import.purchase_id.edi_conversation_id = self.conversation_id
                self.ref = 'purchase.order,%d' % po_import.purchase_id.id
                self.po_id = po_import.purchase_id.id
                self.state = "processed"
                self.process_date = datetime.now()
                return po_import.purchase_id
            else:
                _logger.info("Object Import reported as failure.")
                self.state = "error"
                self.error_text = str(success)
        except WrongTypeError as wte:
            return super(BaseEDITransfer, self).identify_and_import_object()
        except UserError as ue:
            self.state = 'error'
            self.error_text = str(ue)
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            self.state = 'error'
            self.error_text = str(e)

    @api.multi
    def _try_match_po(self, data_dict):
        # get partner
        bdio = self.env['business.document.import']
        partner = bdio._match_partner(
            data_dict['partner'], data_dict['chatter_msg'],
            partner_type='supplier')
        if not partner:
            return False
        data_dict['partner_id'] = partner.id
        po = None
        if 'order_ref' in data_dict:
            po = self.env['purchase.order'].search([('partner_id', '=', partner.id), ('state', 'in', ['draft', 'sent', 'bid]']), ('name', '=', data_dict['order_ref'])])
        if not po:
            po = self.env['purchase.order'].create(data_dict)
        if not po or len(po.ids) > 1:
            return False
        return po