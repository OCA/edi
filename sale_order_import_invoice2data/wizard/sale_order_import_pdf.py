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

    @api.model
    def create_order(self, parsed_order, price_source):
        soo = self.env['sale.order']
        bdio = self.env['business.document.import']
        so_vals = self._prepare_order(parsed_order, price_source)
        order = soo.create(so_vals)
        # attach the PDF to the SO
        if parsed_order['attachments']:
            attachment_vals = {
                'datas':parsed_order['attachments'].values()[0],
                'datas_fname':parsed_order['attachments'].keys()[0],
                'name':parsed_order['attachments'].keys()[0],
                'res_id':order.id,
                'res_model':'sale.order'
            }
            self.env['ir.attachment'].create(attachment_vals)
        bdio.post_create_or_update(parsed_order, order)
        logger.info('Sale Order ID %d created', order.id)
        return order

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

    def compare_lines(
            self, existing_lines, import_lines, chatter_msg,
            qty_precision=None, price_precision=None, seller=False):
        """ Example:
        existing_lines = [{
            'product': odoo_recordset,
            'name': 'USB Adapter',
            'qty': 1.5,
            'price_unit': 23.43,  # without taxes
            'uom': uom,
            'line': recordset,
            # Add taxes
            }]
        import_lines = [{
            'product': {
                'ean13': '2100002000003',
                'code': 'EAZY1',
                },
            'quantity': 2,
            'price_unit': 12.42,  # without taxes
            'uom': {'unece_code': 'C62'},
            }]

        Result of the method:
        {
            'to_remove': line_multirecordset,
            'to_add': [
                {
                    'product': recordset1,
                    'uom', recordset,
                    'import_line': {import dict},
                    # We provide product and uom as recordset to avoid the
                    # need to compute a second match
                ]
            'to_update': {
                'line1_recordset': {'qty': [1, 2], 'price_unit': [4.5, 4.6]},
                # qty must be updated from 1 to 2
                # price must be updated from 4.5 to 4.6
                'line2_recordset': {'qty': [12, 13]},
                # only qty must be updated
                }
        }

        The check existing_currency == import_currency must be done before
        the call to compare_lines()
        """
        dpo = self.env['decimal.precision']
        if qty_precision is None:
            qty_precision = dpo.precision_get('Product Unit of Measure')
        if price_precision is None:
            price_precision = dpo.precision_get('Product Price')
        existing_lines_dict = {}
        for eline in existing_lines:
            if not eline.get('product'):
                chatter_msg.append(_(
                    "The existing line '%s' doesn't have any product, "
                    "so <b>the lines haven't been updated</b>.")
                    % eline.get('name'))
                return False
            if eline['product'] in existing_lines_dict:
                chatter_msg.append(_(
                    "The product '%s' is used on several existing "
                    "lines, so <b>the lines haven't been updated</b>.")
                    % eline['product'].name_get()[0][1])
                return False
            existing_lines_dict[eline['product']] = eline
        unique_import_products = []
        res = {
            'to_remove': False,
            'to_add': [],
            'to_update': {},
            }
        for iline in import_lines:
            # if not iline.get('product'):
            #     chatter_msg.append(_(
            #         "One of the imported lines doesn't have any product, "
            #         "so <b>the lines haven't been updated</b>."))
            #     return False
            product = self._match_product(
                iline, chatter_msg, seller=seller)
            uom = self._match_uom(iline.get('uom'), chatter_msg, product)
            if product in unique_import_products:
                chatter_msg.append(_(
                    "The product '%s' is used on several imported lines, "
                    "so <b>the lines haven't been updated</b>.")
                    % product.name_get()[0][1])
                return False
            unique_import_products.append(product)
            if product in existing_lines_dict:
                if uom != existing_lines_dict[product]['uom']:
                    chatter_msg.append(_(
                        "For product '%s', the unit of measure is %s on the "
                        "existing line, but it is %s on the imported line. "
                        "We don't support this scenario for the moment, so "
                        "<b>the lines haven't been updated</b>.") % (
                            product.name_get()[0][1],
                            existing_lines_dict[product]['uom'].name,
                            uom.name,
                            ))
                    return False
                # used for to_remove
                existing_lines_dict[product]['import'] = True
                oline = existing_lines_dict[product]['line']
                res['to_update'][oline] = {}
                # if float_compare(
                #         iline['qty'],
                #         existing_lines_dict[product]['qty'],
                #         precision_digits=qty_precision): #TODO
                if iline['qty']:
                    res['to_update'][oline]['qty'] = [
                        existing_lines_dict[product]['qty'],
                        iline['qty']]
                # if (
                #         'price_unit' in iline and
                #         float_compare(
                #             iline['price_unit'],
                #             existing_lines_dict[product]['price_unit'],
                #             precision_digits=price_precision)):
                if ('price_unit' in iline and iline['price_unit']):
                    res['to_update'][oline]['price_unit'] = [
                        existing_lines_dict[product]['price_unit'],
                        iline['price_unit']]
            else:
                res['to_add'].append({
                    'product': product,
                    'uom': uom,
                    'import_line': iline,
                    })
        for exiting_dict in existing_lines_dict.itervalues():
            if not exiting_dict.get('import'):
                if res['to_remove']:
                    res['to_remove'] += exiting_dict['line']
                else:
                    res['to_remove'] = exiting_dict['line']
        return res
