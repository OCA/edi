# -*- coding: utf-8 -*-
# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.tools import file_open
import base64


class TestUblOrderImport(TransactionCase):

    def setUp(self):
        super(TestUblOrderImport, self).setUp()
        self.tests = {
            'UBL-Order-2.1-Example.xml': {
                'client_order_ref': '34',
                'date_order': '2010-01-20',
                'partner': self.env.ref('sale_order_import_ubl.johnssons'),
                'shipping_partner':
                self.env.ref('sale_order_import_ubl.swedish_trucking'),
                'currency': self.env.ref('base.SEK'),
                },
            'UBL-Order-2.0-Example.xml': {
                'client_order_ref': 'AEG012345',
                'date_order': '2010-06-20',
                'partner': self.env.ref('sale_order_import_ubl.iyt'),
                'shipping_partner':
                self.env.ref('sale_order_import_ubl.fred_churchill'),
                'currency': self.env.ref('base.GBP'),
                },
            'UBL-Order-2.0-Example_no-party-name.xml': {
                'client_order_ref': 'AEG012345',
                'date_order': '2010-06-20',
                'partner': self.env.ref('sale_order_import_ubl.iyt'),
                'shipping_partner':
                self.env.ref('sale_order_import_ubl.fred_churchill'),
                'currency': self.env.ref('base.GBP'),
                },
            'UBL-RequestForQuotation-2.0-Example.xml': {
                'partner': self.env.ref('sale_order_import_ubl.terminus'),
                'shipping_partner':
                self.env.ref('sale_order_import_ubl.s_massiah'),
                },
            'UBL-RequestForQuotation-2.1-Example.xml': {
                'partner':
                self.env.ref('sale_order_import_ubl.gentofte_kommune'),
                'currency': self.env.ref('base.DKK'),
                'shipping_partner': self.env.ref(
                    'sale_order_import_ubl.delivery_gentofte_kommune'),
                },
            }

    def _check_filename_result(self, filename, res):
        f = file_open(
            'sale_order_import_ubl/tests/files/' + filename, 'rb')
        xml_file = f.read()
        wiz = self.env['sale.order.import'].create({
            'order_file': base64.b64encode(xml_file),
            'order_filename': filename,
        })
        f.close()
        action = wiz.import_order_button()
        so = wiz.sale_id
        if not so:
            so = self.env['sale.order'].browse(action['res_id'])
        self.assertEqual(
            so.partner_id.commercial_partner_id,
            res['partner'])
        if res.get('currency'):
            self.assertEqual(so.currency_id, res['currency'])
        if res.get('client_order_ref'):
            self.assertEqual(so.client_order_ref, res['client_order_ref'])
        if res.get('date_order'):
            self.assertEqual(so.date_order[:10], res['date_order'])
        if res.get('shipping_partner'):
            self.assertEqual(
                so.partner_shipping_id, res['shipping_partner'])

    def test_order_2_0_example(self):
        filename = 'UBL-Order-2.0-Example.xml'
        res = self.tests.get(filename)
        self._check_filename_result(filename, res)

    def test_order_2_0_Example_no_party_name(self):
        filename = 'UBL-Order-2.0-Example_no-party-name.xml'
        res = self.tests.get(filename)
        self._check_filename_result(filename, res)

    def test_order_2_0_Example_existing(self):
        filename = 'UBL-Order-2.0-Example.xml'
        res = self.tests.get(filename)
        self._check_filename_result(filename, res)

        filename = 'UBL-Order-2.0-Example_no-party-name.xml'
        res = self.tests.get(filename)
        self._check_filename_result(filename, res)

    def test_order_2_1_example(self):
        filename = 'UBL-Order-2.1-Example.xml'
        res = self.tests.get(filename)
        self._check_filename_result(filename, res)

    def test_rfq_2_0_example(self):
        filename = 'UBL-RequestForQuotation-2.0-Example.xml'
        res = self.tests.get(filename)
        self._check_filename_result(filename, res)

    def test_rfq_2_1_example(self):
        filename = 'UBL-RequestForQuotation-2.1-Example.xml'
        res = self.tests.get(filename)
        self._check_filename_result(filename, res)
