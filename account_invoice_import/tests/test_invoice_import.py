# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.tools import float_compare


class TestInvoiceImport(TransactionCase):

    def setUp(self):
        super(TestInvoiceImport, self).setUp()
        self.expense_account = self.env['account.account'].create({
            'code': '612AII',
            'name': 'expense account invoice import',
            'user_type_id':
            self.env.ref('account.data_account_type_expenses').id,
        })
        self.income_account = self.env['account.account'].create({
            'code': '707AII',
            'name': 'revenue account invoice import',
            'user_type_id':
            self.env.ref('account.data_account_type_revenue').id,
        })
        purchase_tax_vals = {
            'name': 'Test 1% VAT',
            'description': 'ZZ-VAT-buy-1.0',
            'type_tax_use': 'purchase',
            'amount': 1,
            'amount_type': 'percent',
            'unece_type_id': self.env.ref('account_tax_unece.tax_type_vat').id,
            'unece_categ_id': self.env.ref('account_tax_unece.tax_categ_s').id,
            'account_id': self.expense_account.id,
            'refund_account_id': self.expense_account.id,
        }
        self.purchase_tax = self.env['account.tax'].create(purchase_tax_vals)
        sale_tax_vals = purchase_tax_vals.copy()
        sale_tax_vals.update({
            'description': 'ZZ-VAT-sale-1.0',
            'type_tax_use': 'sale',
        })
        self.sale_tax = self.env['account.tax'].create(sale_tax_vals)
        self.product = self.env['product.product'].create({
            'name': 'Expense product',
            'default_code': 'AII-TEST-PRODUCT',
            'taxes_id': [(6, 0, [self.sale_tax.id])],
            'supplier_taxes_id': [(6, 0, [self.purchase_tax.id])],
            'property_account_income_id': self.income_account.id,
            'property_account_expense_id': self.expense_account.id,
        })
        self.all_import_config = [
            {
                'invoice_line_method': '1line_no_product',
                'account': self.expense_account,
                'taxes': self.purchase_tax,
            },
            {
                'invoice_line_method': '1line_static_product',
                'product': self.product,
            },
            {
                'invoice_line_method': 'nline_no_product',
                'account': self.expense_account,
            },
            {
                'invoice_line_method': 'nline_static_product',
                'product': self.product,
            },
            {
                'invoice_line_method': 'nline_auto_product',
            }
        ]

    def test_import_in_invoice(self):
        parsed_inv = {
            'type': 'in_invoice',
            'amount_untaxed': 100.0,
            'amount_total': 101.0,
            'invoice_number': 'INV-2017-9876',
            'date_invoice': '2017-08-16',
            'date_due': '2017-08-31',
            'date_start': '2017-08-01',
            'date_end': '2017-08-31',
            'partner': {
                'name': 'ASUSTeK',
            },
            'description': 'New hi-tech gadget',
            'lines': [{
                'product': {'code': 'AII-TEST-PRODUCT'},
                'name': 'Super test product',
                'qty': 2,
                'price_unit': 50,
                'taxes': [{
                    'amount_type': 'percent',
                    'amount': 1.0,
                    'unece_type_code': 'VAT',
                    'unece_categ_code': 'S',
                }],
            }]
        }
        for import_config in self.all_import_config:
            self.env['account.invoice.import'].create_invoice(
                parsed_inv, import_config)

    def test_import_out_invoice(self):
        parsed_inv = {
            'type': 'out_invoice',
            'date_invoice': '2017-08-16',
            'partner': {
                'name': 'Agrolait',
            },
            'lines': [{
                'product': {'code': 'AII-TEST-PRODUCT'},
                'name': 'Super product',
                'qty': 3,
                'price_unit': 10.22,
                'date_start': '2017-08-01',
                'date_end': '2017-08-31',
                'taxes': [{  # only needed for method 'nline_no_product'
                    'amount_type': 'percent',
                    'amount': 1.0,
                    'unece_type_code': 'VAT',
                    'unece_categ_code': 'S',
                }],
            }]
        }
        for import_config in self.all_import_config:
            if not import_config['invoice_line_method'].startswith('nline'):
                continue
            inv = self.env['account.invoice.import'].create_invoice(
                parsed_inv, import_config)
            prec = inv.currency_id.rounding
            self.assertFalse(float_compare(
                inv.amount_untaxed, 30.66, precision_rounding=prec))
            self.assertFalse(float_compare(
                inv.amount_total, 30.97, precision_rounding=prec))
