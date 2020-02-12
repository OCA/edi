# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.tools import config
from tempfile import TemporaryFile
from odoo.exceptions import UserError
from base64 import b64encode
import logging
import csv

logger = logging.getLogger(__name__)


class SaleOrderImport(models.TransientModel):
    _name = 'sale.order.import'
    _inherit = ['sale.order.import', 'base.edifact']

    doc_type = fields.Selection(selection_add=[('edifact', 'Edifact')])

    @api.onchange('order_file')
    def order_file_change(self):
        if self.order_filename and self.order_filename.endswith('.pla'):
            self.csv_import = False
            self.doc_type = 'edifact'
            self.price_source = 'order'
        else:
            res = super(SaleOrderImport, self).order_file_change()
            if isinstance(res, dict):
                return res

    @api.model
    def parse_order(self, order_file, order_filename, partner=False):
        assert order_file, 'Missing order file'
        assert order_filename, 'Missing order filename'

        if order_filename.endswith('.pla'):
            # parse pla file:
            parsed_order = self.parse_pla_order(order_file)
            logger.debug('Result of order parsing: %s', parsed_order)
            if 'attachments' not in parsed_order:
                parsed_order['attachments'] = {}
            parsed_order['attachments'][order_filename] = b64encode(order_file)
            if 'chatter_msg' not in parsed_order:
                parsed_order['chatter_msg'] = []
            if (
                    parsed_order.get('company') and
                    not config['test_enable'] and
                    not self._context.get('edi_skip_company_check')):
                self.env['business.document.import']._check_company(
                    parsed_order['company'], parsed_order['chatter_msg'])
        else:
            parsed_order = super(SaleOrderImport, self).parse_order(
                order_file, order_filename, partner)
        return parsed_order

    @api.model
    def parse_pla_order(self, order_file):
        with TemporaryFile(mode='r+') as buf:
            try:
                filename = self.order_filename or '-'
                buf.write(str(order_file, 'iso-8859-1'))
                buf.seek(0)
                csv_iterator = csv.reader(buf, delimiter='|')
                reader = [row for row in csv_iterator]
                if reader[0][0] in (
                        'ORDERS_D_93A_UN_EAN007', 'ORDERS_D_96A_UN_EAN008'):
                    res = self.parse_edifact_sale_order(reader)
                else:
                    raise UserError(
                        _('Unknow Edifact document type: %s.') % (
                            reader[0][0]))
            except Exception as e:
                logger.exception(
                    'Error in File %s: Unsuccessfully imported,'
                    ' due to format mismatch.%s' % (
                        filename, str(e.args[0])))
                raise UserError(
                    _('%s') % (str(e.args[0])))

        return res

    @api.model
    def _prepare_order(self, parsed_order, price_source):
        bdio = self.env['business.document.import']
        partner_obj = self.env['res.partner']

        so_vals = super(SaleOrderImport, self)._prepare_order(
            parsed_order, price_source)
        if 'invoice_to' in parsed_order:
            partner = partner_obj.browse(so_vals['partner_id'])
            invoice_partner = bdio._match_shipping_partner(
                parsed_order['invoice_to'], partner,
                parsed_order['chatter_msg'])
            so_vals['partner_invoice_id'] = invoice_partner.id
        return so_vals

    @api.model
    def parse_edifact_sale_order(self, reader):
        self.price_source = 'order'
        parsed_order = {
            'index': 1,
            'doc_type': 'edifact',
        }
        self.parse_edifact_sale_order_header(reader, parsed_order)
        self.parse_edifact_sale_order_lines(reader, parsed_order)
        # Ignoring 'MOARES' line because it's just a summary

        parsed_order.pop('index')

        return parsed_order

    @api.model
    def parse_edifact_sale_order_header(self, reader, parsed_order):
        index = parsed_order['index']
        segments = reader[index]
        label = segments[0]
        while(label != 'LIN'):
            if label == 'ORD':
                # order number:
                parsed_order['order_ref'] =\
                    self.edifact_parse_order_ref(segments)
            elif label == 'DTM':
                # date:
                parsed_order['date'] = self.edifact_parse_date(segments)
            elif label == 'NADBY':
                # customer partner:
                parsed_order['partner'] = self.edifact_parse_partner(segments)
            elif label == 'NADDP':
                # shipping address:
                parsed_order['ship_to'] = self.edifact_parse_address(segments)
            elif label == 'NADIV':
                # invoice address:
                parsed_order['invoice_to'] =\
                    self.edifact_parse_address(segments)
            elif label == 'CUX':
                # currency
                parsed_order['currency'] =\
                    self.edifact_parse_currency(segments)
            elif label in ('PAI', 'ALI', 'FTX', 'RFF', 'NADMS', 'NADMR',
                           'NADUD', 'CTAXXX', 'COMXXX', 'TAX', 'PAT', 'TOD',
                           'NADPR', 'NADSU'):
                # ignore: not required field
                pass
            else:
                raise UserError(_(
                    "Error reading header: Bad edifact file format"))
            index += 1
            segments = reader[index]
            label = segments[0]
        parsed_order['index'] = index

    @api.model
    def parse_edifact_sale_order_lines(self, reader, parsed_order):
        index = parsed_order['index']
        segments = reader[index]
        label = segments[0]
        parsed_order['lines'] = []
        cur_line = False
        while(label != 'MOARES'):
            if label == 'LIN':
                # new order line:
                if cur_line:
                    parsed_order['lines'].append(cur_line)
                cur_line = {}
                # product
                cur_line['product'] = self.edifact_parse_product(segments)
            elif label == 'QTYLIN':
                # This label can be repeated for the same line.
                self.edifact_parse_quantity(segments, cur_line)
            elif label == 'PRILIN':
                # This label can be repeated for the same line.
                self.edifact_parse_price_unit(segments, cur_line)
            elif label in ('MEALIN', 'DTMLIN', 'FTXLIN', 'PACLIN', 'LOCLIN',
                           'TAXLIN', 'PIALIN', 'IMDLIN', 'MOALIN', 'ALCLIN'):
                # Not required fields
                pass
            else:
                raise UserError(_(
                    "Error reading lines: Bad edifact file format"))
            index += 1
            segments = reader[index]
            label = segments[0]
        if cur_line:
            parsed_order['lines'].append(cur_line)
        parsed_order['index'] = index

    def import_order_button(self):
        try:
            res = super(SaleOrderImport, self).import_order_button()
        except Exception as e:
            logger.exception(
                'Error in File %s: %s' % (
                    self.order_filename, str(e.args[0])))
            raise UserError(
                _('Error in File %s:\n%s') % (
                      self.order_filename, str(e.args[0])))
        return res
