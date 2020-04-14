# -*- coding: utf-8 -*-
# © 2015-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
import base64
from odoo.tools import file_open
from odoo.tools import float_compare


class TestFacturx(TransactionCase):

    def test_import_facturx_invoice(self):
        sample_files = {
            # BASIC
            'ZUGFeRD_1p0_BASIC_Einfach.pdf': {
                'invoice_number': '471102',
                'amount_untaxed': 198.0,
                'amount_total': 235.62,
                'date_invoice': '2013-03-05',
                'partner_xmlid': 'lieferant',
                },
            # Cannot handle BASIC with allowancecharge != 0 and multi-taxes
            # 'ZUGFeRD_1p0_BASIC_Rechnungskorrektur.pdf': {
            #    'type': 'in_refund',
            #    'invoice_number': 'RK21012345',
            #    'amount_untaxed': 7.67,
            #    'amount_total': 8.79,
            #    'date_invoice': '2013-09-16',
            #    'partner_xmlid': 'lieferant',
            #    },
            # COMFORT
            'ZUGFeRD_1p0_COMFORT_Einfach.pdf': {
                'invoice_number': '471102',
                'amount_untaxed': 473.0,
                'amount_total': 529.87,
                'date_invoice': '2013-03-05',
                'date_due': '2013-04-04',
                'partner_xmlid': 'lieferant',
                },
            'ZUGFeRD_1p0_COMFORT_Einfach.pdf-ZUGFeRD-invoice.xml': {
                'invoice_number': '471102',
                'amount_untaxed': 473.0,
                'amount_total': 529.87,
                'date_invoice': '2013-03-05',
                'partner_xmlid': 'lieferant',
                },
            'ZUGFeRD_1p0_COMFORT_Haftpflichtversicherung_'
            'Versicherungssteuer.pdf': {
                'invoice_number': '01.234.567.8-2014-1',
                'amount_untaxed': 50.00,
                'amount_total': 59.50,
                'date_invoice': '2014-01-24',
                # stupid sample files: due date is before invoice date !
                'date_due': '2013-12-06',
                'partner_xmlid': 'mvm_musterhafter',
                },
            'ZUGFeRD_1p0_COMFORT_Kraftfahrversicherung_'
            'Bruttopreise.pdf': {
                'invoice_number': '00.123.456.7-2014-1',
                'amount_untaxed': 184.87,
                'amount_total': 220.0,
                'date_invoice': '2014-03-11',
                'date_due': '2014-04-01',
                'partner_xmlid': 'mvm_musterhafter',
                },
            # Disabled due to a bug in the XML
            # Contains Charge + allowance
            # 'ZUGFeRD_1p0_COMFORT_Rabatte.pdf': {
            #    'invoice_number': '471102',
            #    'amount_untaxed': 193.77,
            # There is a bug in the total amount of the last line
            # (55.46 ; right value is 20 x 2.7700 = 55.40)
            #    'amount_total': 215.14,
            #    'date_invoice': '2013-06-05',
            #    'partner_xmlid': 'lieferant',
            #    },
            # has AllowanceTotalAmount
            'ZUGFeRD_1p0_COMFORT_Rechnungskorrektur.pdf': {
                'type': 'in_refund',
                'invoice_number': 'RK21012345',
                'date_invoice': '2013-09-16',
                'amount_untaxed': 7.67,
                'amount_total': 8.79,
                'partner_xmlid': 'lieferant',
                },
            'ZUGFeRD_1p0_COMFORT_Sachversicherung_berechneter_'
            'Steuersatz.pdf': {
                'invoice_number': '00.123.456.7-2014-1',
                'amount_untaxed': 1000.00,
                'amount_total': 1163.40,
                'date_invoice': '2014-04-18',
                'date_due': '2014-05-21',
                'partner_xmlid': 'mvm_musterhafter',
                },
            'ZUGFeRD_1p0_COMFORT_SEPA_Prenotification.pdf': {
                'invoice_number': '471102',
                'amount_untaxed': 473.00,
                'amount_total': 529.87,
                'date_invoice': '2014-03-05',
                'date_due': '2014-03-20',
                'partner_xmlid': 'lieferant',
                },
            # EXTENDED
            # has AllowanceTotalAmount
            # 'ZUGFeRD_1p0_EXTENDED_Kostenrechnung.pdf': {
            #    'invoice_number': 'KR87654321012',
            #    'amount_untaxed': 1056.05,
            #    'amount_total': 1256.70,
            #    'date_invoice': '2013-10-06',
            #    'partner_xmlid': 'musterlieferant',
            #    },  # disable for a malformed date "20139102"
            'ZUGFeRD_1p0_EXTENDED_Rechnungskorrektur.pdf': {
                'type': 'in_refund',
                'invoice_number': 'RK21012345',
                'amount_untaxed': 7.67,
                'amount_total': 8.79,
                'date_invoice': '2013-09-16',
                'partner_xmlid': 'musterlieferant',
                },
            'ZUGFeRD_1p0_EXTENDED_Warenrechnung.pdf': {
                'invoice_number': 'R87654321012345',
                'amount_untaxed': 448.99,
                'amount_total': 518.99,
                'date_invoice': '2013-08-06',
                'partner_xmlid': 'musterlieferant',
                },
            'Factur-X_MINIMUM-1.xml': {
                'invoice_number': 'INV-1242',
                'amount_untaxed': 100.00,
                'amount_total': 120.00,
                'date_invoice': '2017-08-09',
                'partner_xmlid': 'test_noline',
                },
            'Factur-X_BASIC-1.xml': {
                'invoice_number': 'FA12421242',
                'amount_untaxed': 100.00,
                'amount_total': 120.00,
                'date_invoice': '2017-08-09',
                'partner_xmlid': 'test_line',
                },
            }
        aio = self.env['account.invoice']
        cur_prec = self.env.ref('base.EUR').rounding
        # We need precision of product price at 4
        # in order to import ZUGFeRD_1p0_EXTENDED_Kostenrechnung.pdf
        price_precision = self.env.ref('product.decimal_price')
        price_precision.digits = 4
        for (inv_file, res_dict) in sample_files.iteritems():
            f = file_open(
                'account_invoice_import_factur-x/tests/files/' +
                inv_file, 'rb')
            pdf_file = f.read()
            f.close()
            wiz = self.env['account.invoice.import'].create({
                'invoice_file': base64.b64encode(pdf_file),
                'invoice_filename': inv_file,
                })
            wiz.import_invoice()
            invoices = aio.search([
                ('state', '=', 'draft'),
                ('type', 'in', ('in_invoice', 'in_refund')),
                ('reference', '=', res_dict['invoice_number'])
                ])
            self.assertEqual(len(invoices), 1)
            inv = invoices[0]
            self.assertEqual(inv.type, res_dict.get('type', 'in_invoice'))
            self.assertEqual(inv.date_invoice, res_dict['date_invoice'])
            if res_dict.get('date_due'):
                self.assertEqual(inv.date_due, res_dict['date_due'])
            self.assertEqual(inv.partner_id, self.env.ref(
                'account_invoice_import_factur-x.' +
                res_dict['partner_xmlid']))
            self.assertFalse(float_compare(
                inv.amount_untaxed, res_dict['amount_untaxed'],
                precision_rounding=cur_prec))
            self.assertFalse(float_compare(
                inv.amount_total, res_dict['amount_total'],
                precision_rounding=cur_prec))
            # Delete because several sample invoices have the same number
            invoices.unlink()
