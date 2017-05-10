# -*- coding: utf-8 -*-
# © 2016 Sunflower IT (http://sunflowerweb.nl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, tools, _
from openerp.exceptions import Warning as UserError
from openerp.tools import float_compare
from tempfile import mkstemp
import base64
import unicodecsv
import os
import re
import pkg_resources
import logging
logger = logging.getLogger(__name__)

try:
    import unicodecsv
except ImportError:
    logger.debug('Cannot import unicodecsv')

try:
    from invoice2data.main import extract_data
    from invoice2data.template import read_templates
    from invoice2data.main import logger as loggeri2data
except ImportError:
    logger.debug('Cannot import invoice2data')


class SaleOrderImport(models.TransientModel):
    _inherit = 'sale.order.import'

    # @api.model
    # def fallback_parse_pdf_saleorder(self, file_data):
    #     '''This method must be inherited by additionnal modules with
    #     the same kind of logic as the account_bank_statement_import_*
    #     modules'''
    #     return self.invoice2data_parse_saleorder(file_data)
    #
    @api.model
    def parse_pdf_order(self, file_data, detect_doc_type=False):
        logger.info('Trying to analyze PDF saleorder with invoice2data lib')
        if detect_doc_type:
            return 'rfq'
        fd, file_name = mkstemp()
        try:
            os.write(fd, file_data)
        finally:
            os.close(fd)
        # Transfer log level of Odoo to invoice2data
        loggeri2data.setLevel(logger.getEffectiveLevel())
        local_templates_dir = tools.config.get(
            'invoice2data_templates_dir', False)
        logger.debug(
            'invoice2data local_templates_dir=%s', local_templates_dir)
        templates = []
        if local_templates_dir and os.path.isdir(local_templates_dir):
            templates += read_templates(local_templates_dir)
        exclude_built_in_templates = tools.config.get(
            'invoice2data_exclude_built_in_templates', False)
        if not exclude_built_in_templates:
            templates += read_templates(
                pkg_resources.resource_filename('invoice2data', 'templates'))
        logger.debug(
            'Calling invoice2data.extract_data with templates=%s',
            templates)
        testspath = os.path.dirname(os.path.realpath(__file__))
        templ_path = os.path.join(testspath, '../templates')
        file_path = os.path.join(testspath, 'files', file_name)
        templates += read_templates(templ_path)
        try:
            invoice2data_res = extract_data(file_name, templates=templates)
        except Exception, e:
            raise UserError(_(
                "PDF saleorder parsing failed. Error message: %s") % e)
        if not invoice2data_res:
            raise UserError(_(
                "This PDF saleorder doesn't match a known template of "
                "the invoice2data lib."))
        logger.info(
            'Result of invoice2data PDF extraction: %s', invoice2data_res)
        return self.invoice2data_to_parsed_order(invoice2data_res)

    @api.model
    def invoice2data_to_parsed_order(self, invoice2data_res):
        precision = self.env['decimal.precision'].precision_get('Product UoS')
        parsed_order = {
            'partner': {
                'vat': invoice2data_res.get('vat'),
                'name': invoice2data_res.get('partner_name'),
                'email': invoice2data_res.get('partner_email'),
                'website': invoice2data_res.get('partner_website'),
                'siren': invoice2data_res.get('siren'),
            },
            'currency': {
                'iso': invoice2data_res.get('currency'),
            },
            'amount_total': invoice2data_res.get('amount'),
            'saleorder_number': invoice2data_res.get('invoice_number'),
            'date': invoice2data_res.get('date'),
            'date_due': invoice2data_res.get('date_due'),
            'date_start': invoice2data_res.get('date_start'),
            'date_end': invoice2data_res.get('date_end'),
            'description': invoice2data_res.get('description'),
        }
        if 'amount_untaxed' in invoice2data_res:
            parsed_order['amount_untaxed'] = invoice2data_res['amount_untaxed']
        if 'lines' in invoice2data_res:
            parsed_order['lines'] = []
            for i, line in enumerate(invoice2data_res['lines']):
                vals = {
                    # TODO: bdio.compare_lines() expects
                    # this way,
                    'product': {
                        'desc': line.get('desc'),
                        'code': line.get('code'),
                        'ean13': line.get('ean13'),
                    },
                    # sale_order_import expects this way,
                    'desc': line.get('desc'),
                    'code': line.get('code'),
                    'ean13': line.get('ean13'),
                    # --------------
                    'taxes': line.get('taxes'),
                    'unit_price': line.get('unit_price'),
                    'price': line.get('price'),
                }
                # Quantity
                try:
                    qty = float(line.get('qty'))
                except:
                    raise UserError(_(
                        "Error on PDF order line %d: The quantity should "
                        "use dot as decimal separator and shouldn't have any "
                        "thousand separator") % i)
                if float_compare(qty, 0, precision_digits=precision) != 1:
                    raise UserError(_(
                        "Error on PDF order line %d: the quantity should "
                        "be strictly positive") % i)
                vals['qty'] = qty
                parsed_order['lines'].append(vals)
        if 'amount_tax' in invoice2data_res:
            parsed_order['amount_tax'] = invoice2data_res['amount_tax']
        return parsed_order

    @api.model
    def create_order(self, parsed_order, price_source):
        bdio = self.env['business.document.import']
        so_vals = self._prepare_order(parsed_order, price_source)
        order = self.env['sale.order'].create(so_vals)
        bdio.post_create_or_update(parsed_order, order)
        logger.info('Sale Order ID %d created', order.id)
        return order


class BusinessDocumentImport(models.AbstractModel):
    _inherit = 'business.document.import'

    @api.model
    def _match_product(self, product_dict, chatter_msg, seller=False):
        """
        Extension to support product search on name
        TODO: submit as a PR to business_document_import
        """
        ppo = self.env['product.product']
        self._strip_cleanup_dict(product_dict)
        if product_dict.get('desc'):
            desc = product_dict['desc']
            products = ppo.search([
                ('name', '=', desc)])
            if not products:
                # Also try the part outside brackets only
                stripped_desc = re.sub(
                    "[\(\[].*?[\)\]]", "", desc).strip()
                products = ppo.search([
                    ('name', '=', stripped_desc)])
            if products:
                return products[0]
        return super(BusinessDocumentImport, self)._match_product(
            product_dict, chatter_msg, seller=seller)
