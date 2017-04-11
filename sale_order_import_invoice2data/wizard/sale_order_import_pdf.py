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
        # if not exclude_built_in_templates:
        #     templates += read_templates(
        #         pkg_resources.resource_filename('invoice2data', 'templates'))
        # logger.debug(
        #     'Calling invoice2data.extract_data with templates=%s',
        #     templates)
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
        return self.invoice2data_to_parsed_inv(invoice2data_res)

    @api.model
    def invoice2data_to_parsed_inv(self, invoice2data_res):
        parsed_inv = {
            'partner': {
                'vat': invoice2data_res.get('vat'),
                #'name': invoice2data_res.get('partner'),
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
            parsed_inv['amount_untaxed'] = invoice2data_res['amount_untaxed']
        if 'lines' in invoice2data_res:
            parsed_inv['lines'] = invoice2data_res['lines']
        if 'amount_tax' in invoice2data_res:
            parsed_inv['amount_tax'] = invoice2data_res['amount_tax']
        return parsed_inv

class BusinessDocumentExtend(models.AbstractModel):
    _inherit = 'business.document.import'

    @api.model
    def _match_product(self, product_dict, chatter_msg, seller=False):
        """Example:
        product_dict = {
            'ean13': '5449000054227',
            'code': 'COCA1L',
            }
        """
        ppo = self.env['product.product']
        # self._strip_cleanup_dict(product_dict)
        if product_dict.get('recordset'):
            return product_dict['recordset']
        if product_dict.get('id'):
            return ppo.browse(product_dict['id'])
        if product_dict.get('ean13'):
            products = ppo.search([
                ('ean13', '=', product_dict['ean13'])])
            if products:
                return products[0]
        if product_dict.get('name'):
            products = ppo.search([
                ('name', '=', product_dict['name'])])
            if products:
                return products[0]
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
        if product_dict.get('code'):
            products = ppo.search([
                '|',
                ('ean13', '=', product_dict['code']),
                ('default_code', '=', product_dict['code'])])
            if products:
                return products[0]
            # WARNING: Won't work for multi-variant products
            # because product.supplierinfo is attached to product template
            if seller:
                sinfo = self.env['product.supplierinfo'].search([
                    ('name', '=', seller.id),
                    ('product_code', '=', product_dict['code']),
                    ])
                if (
                        sinfo and
                        sinfo[0].product_tmpl_id.product_variant_ids and
                        len(
                        sinfo[0].product_tmpl_id.product_variant_ids) == 1
                        ):
                    return sinfo[0].product_tmpl_id.product_variant_ids[0]

        raise UserError(_(
            "Odoo couldn't find any product corresponding to the "
            "following information extracted from the business document: "
            "EAN13: %s\n"
            "Product code: %s\n"
            "Supplier: %s\n") % (
                product_dict.get('ean13'),
                product_dict.get('code'),
                seller and seller.name or 'None'))