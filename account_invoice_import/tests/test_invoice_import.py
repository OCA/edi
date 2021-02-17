# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.tools import float_compare
from mock import Mock


class TestInvoiceImport(TransactionCase):

    def setUp(self):
        super().setUp()
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
        sale_tax_vals = {
            'name': 'Test 1% VAT',
            'description': 'ZZ-VAT-buy-1.0',
            'type_tax_use': 'sale',
            'amount': 1,
            'amount_type': 'percent',
            'unece_type_id': self.env.ref('account_tax_unece.tax_type_vat').id,
            'unece_categ_id': self.env.ref('account_tax_unece.tax_categ_s').id,
            'account_id': self.income_account.id,
            'refund_account_id': self.income_account.id,
        }
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
        self.all_import_config_sale = [
            {
                'invoice_line_method': '1line_no_product',
                'account': self.income_account,
                'taxes': self.sale_tax,
            },
            {
                'invoice_line_method': '1line_static_product',
                'product': self.product,
            },
            {
                'invoice_line_method': 'nline_no_product',
                'account': self.income_account,
            },
            {
                'invoice_line_method': 'nline_static_product',
                'product': self.product,
            },
            {
                'invoice_line_method': 'nline_auto_product',
            }
        ]
        self.parsed_inv_out = {
            'type': 'out_invoice',
            'date_invoice': '2017-08-16',
            'partner': {
                'name': 'Wood Corner',
            },
            'lines': [{
                'product': {'code': 'AII-TEST-PRODUCT'},
                'name': 'Super product',
                'qty': 2,
                'price_unit': 50,
                'date_start': '2017-08-01',
                'date_end': '2017-08-31',
                'taxes': [{  # only needed for method 'nline_no_product'
                    'amount_type': 'percent',
                    'amount': 1.0,
                    'unece_type_code': 'VAT',
                    'unece_categ_code': 'S',
                }],
            }],
            'chatter_msg': [],
            'currency': {},
            'amount_untaxed': 100.0,
            'amount_total': 101.0
        }
        self.parsed_inv_in = {
            'type': 'in_invoice',
            'invoice_number': 'INV-2017-9876',
            'date_invoice': '2017-08-16',
            'date_due': '2017-08-31',
            'date_start': '2017-08-01',
            'date_end': '2017-08-31',
            'partner': {
                'name': 'Wood Corner',
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
            }],
            'chatter_msg': [],
            'currency': {},
            'amount_untaxed': 100.0,
            'amount_total': 101.0
        }

    def test_import_in_invoice(self):
        partner = self.env['res.partner'].search([
            ('name', '=', 'Wood Corner')
        ])
        all_import_config_create = [{
            'name': 'test', 'partner_id': partner.id,
            'account_id': self.all_import_config[0]['account'].id,
            'tax_ids': [(6, 0, [self.purchase_tax.id])],
            'invoice_line_method': self.all_import_config[0]['invoice_line_method'],
            'type': 'supplier',
        }, {
            'name': 'test1', 'partner_id': partner.id,
            'static_product_id': self.all_import_config[1]['product'].id,
            'invoice_line_method': self.all_import_config[1]['invoice_line_method'],
            'type': 'supplier',
        }, {
            'name': 'test2', 'partner_id': partner.id,
            'account_id': self.all_import_config[2]['account'].id,
            'invoice_line_method': self.all_import_config[2]['invoice_line_method'],
            'type': 'supplier',
        }, {
            'name': 'test3', 'partner_id': partner.id,
            'static_product_id': self.all_import_config[3]['product'].id,
            'invoice_line_method': self.all_import_config[3]['invoice_line_method'],
            'type': 'supplier',
        }, {
            'name': 'test4', 'partner_id': partner.id,
            'invoice_line_method': self.all_import_config[4]['invoice_line_method'],
            'type': 'supplier',
        }]
        for import_config_dict in all_import_config_create:
            import_config = self.env['account.invoice.import.config'].create(
                import_config_dict
            )
            wiz = self.env['account.invoice.import'].create({
                'invoice_filename': 'test.xml',
                'import_config_id': import_config.id,
                'invoice_file': b'0000'
            })
            wiz.parse_invoice = Mock(return_value=self.parsed_inv_in)
            action = wiz.import_invoice()
            inv = self.env['account.invoice'].browse(action['res_id'])
            prec = inv.currency_id.rounding
            self.assertFalse(float_compare(
                inv.amount_untaxed, 100, precision_rounding=prec))
            self.assertFalse(float_compare(
                inv.amount_total, 101, precision_rounding=prec))
            inv.unlink()

    def test_create_in_invoice(self):
        for import_config in self.all_import_config:
            inv = self.env['account.invoice.import'].create_invoice(
                self.parsed_inv_in, import_config)
            if not import_config['invoice_line_method'].startswith('nline'):
                continue
            prec = inv.currency_id.rounding
            self.assertFalse(float_compare(
                inv.amount_untaxed, 100, precision_rounding=prec))
            self.assertFalse(float_compare(
                inv.amount_total, 101, precision_rounding=prec))

    def test_create_out_invoice(self):
        partner = self.env['res.partner'].search([
            ('name', '=', 'Wood Corner')
        ])
        partner.customer = True

        for import_config in self.all_import_config_sale:
            inv = self.env['account.invoice.import'].create_invoice(
                self.parsed_inv_out, import_config)
            prec = inv.currency_id.rounding
            if not import_config['invoice_line_method'].startswith('nline'):
                continue
            self.assertFalse(float_compare(
                inv.amount_untaxed, 100, precision_rounding=prec))
            self.assertFalse(float_compare(
                inv.amount_total, 101, precision_rounding=prec))

    def test_import_out_invoice(self):
        partner = self.env['res.partner'].search([
            ('name', '=', 'Wood Corner')
        ])
        partner.customer = True
        all_import_config_create = [{
            'name': 'test', 'partner_id': partner.id,
            'account_id': self.all_import_config_sale[0]['account'].id,
            'tax_ids': [(6, 0, [self.sale_tax.id])],
            'invoice_line_method': (
                self.all_import_config_sale[0]['invoice_line_method']
            ),
            'type': 'customer',
        }, {
            'name': 'test1', 'partner_id': partner.id,
            'static_product_id': self.all_import_config_sale[1]['product'].id,
            'invoice_line_method': (
                self.all_import_config_sale[1]['invoice_line_method']
            ),
            'type': 'customer',
        }, {
            'name': 'test2', 'partner_id': partner.id,
            'account_id': self.all_import_config_sale[2]['account'].id,
            'invoice_line_method': (
                self.all_import_config_sale[2]['invoice_line_method']
            ),
            'type': 'customer',
        }, {
            'name': 'test3', 'partner_id': partner.id,
            'static_product_id': self.all_import_config_sale[3]['product'].id,
            'invoice_line_method': (
                self.all_import_config_sale[3]['invoice_line_method']
            ),
            'type': 'customer',
        }, {
            'name': 'test4', 'partner_id': partner.id,
            'invoice_line_method': (
                self.all_import_config_sale[4]['invoice_line_method']
            ),
            'type': 'customer',
        }]
        for import_config_dict in all_import_config_create:
            import_config = self.env['account.invoice.import.config'].create(
                import_config_dict
            )
            wiz = self.env['account.invoice.import'].create({
                'invoice_filename': 'test.xml',
                'import_config_id': import_config.id,
                'invoice_file': b'0000'
            })
            wiz.parse_invoice = Mock(return_value=self.parsed_inv_out)
            action = wiz.import_invoice()
            inv = self.env['account.invoice'].browse(action['res_id'])
            prec = inv.currency_id.rounding
            self.assertFalse(float_compare(
                inv.amount_untaxed, 100, precision_rounding=prec))
            self.assertFalse(float_compare(
                inv.amount_total, 101, precision_rounding=prec))
            inv.unlink()
