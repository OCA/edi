# -*- coding: utf-8 -*-
# © 2016 Sunflower IT (http://sunflowerweb.nl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os
from tempfile import mkstemp

from openerp import models, api, _
from openerp.exceptions import Warning as UserError
from openerp.tools import float_compare

logger = logging.getLogger(__name__)
try:
    from invoice2data.main import extract_data
    from invoice2data.main import logger as loggeri2data
except ImportError:
    logger.debug('Cannot import invoice2data')


class SaleOrderImport(models.TransientModel):
    _inherit = 'sale.order.import'

    @api.model
    def collect_pdf_templates(self):
        """ Create a collection of templates """
        return self.env['invoice2data.template'].get_templates('sale_order')

    @api.model
    def parse_pdf_order(self, file_data, detect_doc_type=False):
        """ Parse Sale order PDF with invoice2data """
        logger.info('Trying to analyze PDF saleorder with invoice2data lib')

        # document type is RFQ
        if detect_doc_type:
            return 'rfq'

        # Write PDF contents to temp file
        fd, file_name = mkstemp()
        try:
            os.write(fd, file_data)
        finally:
            os.close(fd)

        # Transfer log level of Odoo to invoice2data
        loggeri2data.setLevel(logger.getEffectiveLevel())

        # Try to use invoice2data to parse file
        templates = self.collect_pdf_templates()
        invoice2data_res = None
        try:
            invoice2data_res = extract_data(file_name, templates=templates)
            if not invoice2data_res:
                logger.info(_(
                    "This PDF saleorder doesn't match a known template of "
                    "the invoice2data lib."))
        except Exception as e:
            logger.info(_(
                "PDF saleorder parsing failed. Error message: %s") % e)

        # Remove temp file
        os.remove(file_name)

        # Failure
        if not invoice2data_res:
            # Try other kinds of PDF parsing
            return super(
                SaleOrderImport, self
            ).parse_pdf_order(file_data, detect_doc_type)

        # Success, return parsed sale order
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
