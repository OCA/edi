# -*- coding: utf-8 -*-
# © 2016 Sunflower IT (http://sunflowerweb.nl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase
from openerp.tools import file_open, float_compare
from tempfile import mkstemp
import base64
import os
import logging
logger = logging.getLogger(__name__)

try:
    from invoice2data.main import extract_data
    from invoice2data.template import read_templates
    from invoice2data.main import logger as loggeri2data
except ImportError:
    logger.debug('Cannot import invoice2data')

class TestPDFOrderImport(TransactionCase):

    def read_pdf_and_create_wizard(self, filename, partner):
        soio = self.env['sale.order.import']
        f = file_open(
            'sale_order_import_saleorder2data/tests/files/' + filename, 'rb')
        pdf_file = f.read()
        wiz = soio.create({
            'order_file': base64.b64encode(pdf_file),
            'order_filename': filename,
            'partner_id': partner.id,
        })
        f.close()
        templates = read_templates('sale_order_import_saleorder2data/templates/')
        get_data = soio.extract_data(pdf_file, templates)
        pdf_file_content = {}
        f.seek(0)
        for line in get_data:
            pdf_file_content[line[0]] = float(line[1])

        return pdf_file_content, wiz

    def check_sale_order(self, order, pdf_file_content, partner):
        precision = self.env['decimal.precision'].precision_get('Product UoS')
        self.assertEqual(order.partner_id, partner)
        self.assertEqual(len(order.order_line), len(pdf_file_content))
        for oline in order.order_line:
            self.assertFalse(
                float_compare(
                    pdf_file_content[oline.product_id.default_code],
                    oline.product_uom_qty,
                    precision_digits=precision))

    def test_pdf_order_import(self):
        # create new quote
        filename = 'so1.pdf'
        partner = self.env.ref('base.res_partner_2')
        pdf_file_content, wiz = self.read_csv_and_create_wizard(
            filename, partner)
        action = wiz.import_order_button()
        so = self.env['sale.order'].browse(action['res_id'])
        self.check_sale_order(so, pdf_file_content, partner)

        wiz = self.read_pdf_and_create_wizard(
                filename, partner)
        action = wiz.import_order_button()
        so = self.env['sale.order'].browse(action['res_id'])

        # update existing quote
        filename_up = 'so2.pdf'
        pdf_file_content_up, wiz_up = self.read_csv_and_create_wizard(
            filename_up, partner)
        action_up1 = wiz_up.import_order_button()
        self.assertEqual(action_up1['res_model'], 'sale.order.import')
        self.assertEqual(wiz_up.sale_id, so)
        action_up2 = wiz_up.update_order_button()
        self.assertEqual(action_up2['res_model'], 'sale.order')
        self.check_sale_order(so, pdf_file_content_up, partner)
