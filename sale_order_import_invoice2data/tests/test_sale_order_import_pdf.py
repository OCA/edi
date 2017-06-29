# -*- coding: utf-8 -*-
# © 2016 Sunflower IT (http://sunflowerweb.nl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os
import logging

from openerp.tests.common import TransactionCase
from openerp.tools import file_open, float_compare

logger = logging.getLogger(__name__)
try:
    from invoice2data.main import extract_data
except ImportError:
    logger.debug('Cannot import invoice2data')


class TestPDFOrderImport(TransactionCase):

    def setUp(self):
        super(TestPDFOrderImport, self).setUp()
        self.soio = self.env['sale.order.import']
        self.camptocamp = self.env.ref('base.res_partner_12')

    def read_pdf_and_create_wizard(self, file_name):
        soio = self.env['sale.order.import']
        testspath = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(testspath, 'files', file_name)
        f = file_open(file_path, 'rb')
        pdf_file = f.read()
        wiz = soio.create({
            'order_file': base64.b64encode(pdf_file),
            'order_filename': file_name,
        })
        f.close()
        templates = self.env['invoice2data.template'].get_templates(
            'sale_order'
        )
        get_data = extract_data(file_path, templates=templates)
        pdf_file_content = get_data

        return pdf_file_content, wiz

    def check_sale_order(self, order, pdf_file_content, partner):
        precision = self.env['decimal.precision'].precision_get('Product UoS')
        self.assertEqual(order.partner_id, partner)
        self.assertEqual(len(order.order_line),
                         len(pdf_file_content['lines']))
        for i, oline in enumerate(order.order_line):
            self.assertFalse(
                float_compare(
                    float(pdf_file_content['lines'][i]['qty']),
                    oline.product_uom_qty,
                    precision_digits=precision))
        # check if attachment of created SO
        attachment = self.env['ir.attachment'].search([
            ('res_id', '=', order.id),
            ('res_name', 'like', order.name)
        ])
        self.assertTrue(attachment)

    def test_pdf_order_import(self):
        # Import a sale order for a partner with no existing quotes
        # (In the demo database, that is Camptocamp)
        filename = 'so1.pdf'
        pdf_file_content, wiz = self.read_pdf_and_create_wizard(filename)
        action = wiz.import_order_button()
        self.assertEqual(action['res_model'], 'sale.order')

        # Check if the quotation has been imported well
        so = self.env['sale.order'].browse(action['res_id'])
        self.check_sale_order(so, pdf_file_content, self.camptocamp)

        # Update an existing quotation for the imported partner
        # Again we use Camptocamp, which now has a quotation
        filename_up = 'so2.pdf'
        pdf_file_content_up, wiz_up = self.read_pdf_and_create_wizard(
            filename_up)
        action_up1 = wiz_up.import_order_button()

        # Check if we are getting the existing quotation to choose from
        self.assertEqual(action_up1['res_model'], 'sale.order.import')
        self.assertEqual(wiz_up.sale_id, so)

        # Update the quotation
        action_up2 = wiz_up.update_order_button()
        self.assertEqual(action_up2['res_model'], 'sale.order')

        # Check if the quotation has been updated well
        self.check_sale_order(so, pdf_file_content_up, self.camptocamp)
