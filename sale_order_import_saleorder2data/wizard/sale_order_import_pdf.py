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

    @api.model
    def fallback_parse_pdf_saleorder(self, file_data):
        '''This method must be inherited by additionnal modules with
        the same kind of logic as the account_bank_statement_import_*
        modules'''
        return self.saleorder2data_parse_saleorder(file_data)

    @api.model
    def parse_pdf_order(self, file_data):
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
        if not exclude_built_in_templates:
            templates += read_templates(
                pkg_resources.resource_filename('invoice2data', 'templates'))
        logger.debug(
            'Calling invoice2data.extract_data with templates=%s',
            templates)
        try:
            saleorder2data_res = extract_data(file_name, templates=templates)
        except Exception, e:
            raise UserError(_(
                "PDF saleorder parsing failed. Error message: %s") % e)
        if not saleorder2data_res:
            raise UserError(_(
                "This PDF saleorder doesn't match a known template of "
                "the invoice2data lib."))
        logger.info(
            'Result of invoice2data PDF extraction: %s', saleorder2data_res)
        return self.saleorder2data_to_parsed_inv(saleorder2data_res)

    @api.model
    def saleorder2data_to_parsed_inv(self, saleorder2data_res):
        parsed_inv = {
            'partner': {
                'vat': saleorder2data_res.get('vat'),
                'name': saleorder2data_res.get('partner_name'),
                'email': saleorder2data_res.get('partner_email'),
                'website': saleorder2data_res.get('partner_website'),
                'siren': saleorder2data_res.get('siren'),
            },
            'currency': {
                'iso': saleorder2data_res.get('currency'),
            },
            'amount_total': saleorder2data_res.get('amount'),
            'saleorder_number': saleorder2data_res.get('invoice_number'),
            'date': saleorder2data_res.get('date'),
            'date_due': saleorder2data_res.get('date_due'),
            'date_start': saleorder2data_res.get('date_start'),
            'date_end': saleorder2data_res.get('date_end'),
            'description': saleorder2data_res.get('description'),
        }
        if 'amount_untaxed' in saleorder2data_res:
            parsed_inv['amount_untaxed'] = saleorder2data_res['amount_untaxed']
        if 'amount_tax' in saleorder2data_res:
            parsed_inv['amount_tax'] = saleorder2data_res['amount_tax']
        return parsed_inv
