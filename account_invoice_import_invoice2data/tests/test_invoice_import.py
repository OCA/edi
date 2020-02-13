# Copyright 2015-2020 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.tools import file_open, float_compare
from odoo import fields
import base64


class TestInvoiceImport(TransactionCase):

    def setUp(self):
        super(TestInvoiceImport, self).setUp()
        frtax = self.env['account.tax'].create({
            'name': 'French VAT purchase 20.0%',
            'description': 'FR-VAT-buy-20.0',
            'amount': 20,
            'amount_type': 'percent',
            'account_id': self.env['account.account'].search([
                ('user_type_id', '=',
                 self.env.ref('account.data_account_type_expenses').id)
            ], limit=1).id,
            'refund_account_id': self.env['account.account'].search([
                ('user_type_id', '=',
                 self.env.ref('account.data_account_type_expenses').id)
            ], limit=1).id,
            'type_tax_use': 'purchase',
            })
        # Set this tax on Internet access product
        internet_product = self.env.ref(
            'account_invoice_import_invoice2data.internet_access')
        internet_product.supplier_taxes_id = [(6, 0, [frtax.id])]

    def test_import_free_invoice(self):
        filename = 'invoice_free_fiber_201507.pdf'
        f = file_open(
            'account_invoice_import_invoice2data/tests/pdf/' + filename, 'rb')
        pdf_file = f.read()
        wiz = self.env['account.invoice.import'].create({
            'invoice_file': base64.b64encode(pdf_file),
            'invoice_filename': filename,
        })
        f.close()
        wiz.import_invoice()
        # Check result of invoice creation
        invoices = self.env['account.invoice'].search([
            ('state', '=', 'draft'),
            ('type', '=', 'in_invoice'),
            ('reference', '=', '562044387')
            ])
        self.assertEquals(len(invoices), 1)
        inv = invoices[0]
        self.assertEquals(inv.type, 'in_invoice')
        self.assertEquals(
            fields.Date.to_string(inv.date_invoice), '2015-07-02')
        self.assertEquals(
            inv.partner_id,
            self.env.ref('account_invoice_import_invoice2data.free'))
        self.assertEquals(inv.journal_id.type, 'purchase')
        self.assertEquals(
            float_compare(inv.amount_total, 29.99, precision_digits=2), 0)
        self.assertEquals(
            float_compare(inv.amount_untaxed, 24.99, precision_digits=2), 0)
        self.assertEquals(
            len(inv.invoice_line_ids), 1)
        iline = inv.invoice_line_ids[0]
        self.assertEquals(iline.name, 'Fiber optic access at the main office')
        self.assertEquals(
            iline.product_id,
            self.env.ref(
                'account_invoice_import_invoice2data.internet_access'))
        self.assertEquals(
            float_compare(iline.quantity, 1.0, precision_digits=0), 0)
        self.assertEquals(
            float_compare(iline.price_unit, 24.99, precision_digits=2), 0)

        # Prepare data for next test i.e. invoice update
        # (we re-use the invoice created by the first import !)
        inv.write({
            'date_invoice': False,
            'reference': False,
            })

        # New import with update of an existing draft invoice
        f = file_open(
            'account_invoice_import_invoice2data/tests/pdf/'
            'invoice_free_fiber_201507.pdf',
            'rb')
        pdf_file = f.read()
        wiz2 = self.env['account.invoice.import'].create({
            'invoice_file': base64.b64encode(pdf_file),
            'invoice_filename': 'invoice_free_fiber_201507.pdf',
            })
        f.close()
        action = wiz2.import_invoice()
        self.assertEquals(
            action['res_model'], 'account.invoice.import')
        # Choose to update the existing invoice
        wiz2.update_invoice()
        invoices = self.env['account.invoice'].search([
            ('state', '=', 'draft'),
            ('type', '=', 'in_invoice'),
            ('reference', '=', '562044387')
            ])
        self.assertEquals(len(invoices), 1)
        inv = invoices[0]
        self.assertEquals(
            fields.Date.to_string(inv.date_invoice), '2015-07-02')
