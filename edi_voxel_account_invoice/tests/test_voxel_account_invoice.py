# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime
from odoo.tests import common


class TestVoxelAccountInvoice(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestVoxelAccountInvoice, cls).setUpClass()
        # Invoice line account
        account_type_revenue = cls.env.ref('account.data_account_type_revenue')
        account_revenue = cls.env['account.account'].search(
            [('user_type_id', '=', account_type_revenue.id)], limit=1)
        # Invoice company
        main_company = cls.env.ref('base.main_company')
        main_company.write({'vat': 'US1234567890', 'street2': 'Street 2'})
        # Invoice client
        partner = cls.env["res.partner"].create({
            'ref': 'C01',
            'vat': 'BE0123456789',
            'name': 'Client (test)',
            'email': 'client_test@example.com',
            'street': 'Street 1',
            'street2': 'Street 2',
            'city': 'City (test)',
            'zip': '10000',
            'state_id': cls.env.ref("base.state_us_49").id,
            'country_id': cls.env.ref("base.us").id,
        })
        # Invoice products
        product_obj = cls.env["product.product"]
        product_1 = product_obj.create({
            'default_code': 'DC_001',
            'name': 'Product 1 (test)',
        })
        cls.env['product.customerinfo'].create({
            'name': partner.id,
            'product_tmpl_id': product_1.product_tmpl_id.id,
            'product_id': product_1.id,
            'product_code': '1234567891234',
        })
        product_2 = product_obj.create({
            'default_code': 'DC_002',
            'name': 'Product 2 (test)',
        })
        product_3 = product_obj.create({
            'default_code': 'DC_003',
            'name': 'Product 3 (test)',
        })
        # Invoice
        cls.invoice = cls.env['account.invoice'].create({
            'partner_id': partner.id,
            'type': 'out_invoice',
            'currency_id': cls.env.ref('base.USD').id,
            'date_invoice': date(2019, 4, 13),
            'company_id': main_company.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': product_1.id,
                    'quantity': 2,
                    'price_unit': 750,
                    'name': 'Product 1',
                    'uom_id': cls.env.ref('uom.product_uom_unit').id,
                    'account_id': account_revenue.id,
                }),
                (0, 0, {
                    'product_id': product_2.id,
                    'quantity': 3,
                    'price_unit': 147,
                    'discount': 20,
                    'invoice_line_tax_ids': [
                        (0, None, {
                            'name': 'Tax 15%',
                            'type_tax_use': 'sale',
                            'amount_type': 'percent',
                            'amount': 15,
                            'tax_group_id': cls.env.ref(
                                'account.tax_group_taxes').id,
                        }),
                        (0, None, {
                            'name': 'Tax 30.00%',
                            'type_tax_use': 'sale',
                            'amount_type': 'percent',
                            'amount': 30,
                            'tax_group_id': cls.env.ref(
                                'account.tax_group_taxes').id,
                        }),
                    ],
                    'name': 'Product 2',
                    'uom_id': cls.env.ref('uom.product_uom_unit').id,
                    'account_id': account_revenue.id,
                }),
                (0, 0, {
                    'product_id': product_3.id,
                    'quantity': 0,
                    'price_unit': 0,
                    'name': 'Product 3',
                    'uom_id': cls.env.ref('uom.product_uom_unit').id,
                    'account_id': account_revenue.id,
                }),
            ]
        })

    def test_get_voxel_filename(self):
        bef = datetime.now()
        bef = datetime(bef.year, bef.month, bef.day, bef.hour, bef.minute,
                       bef.second, (bef.microsecond // 1000) * 1000)
        filename = self.invoice._get_voxel_filename()
        document_type, date_time = filename[:-4].split('_', 1)
        date_time = datetime.strptime(date_time, '%Y%m%d_%H%M%S_%f')
        self.assertEqual(document_type, 'Factura')
        self.assertGreaterEqual(date_time, bef)
        # Commented because it raise random error in pipeline tests
        # aft = datetime.now()
        # aft = datetime(aft.year, aft.month, aft.day, aft.hour, aft.minute,
        #                aft.second, (bef.microsecond // 1000) * 1000)
        # self.assertLessEqual(date_time, aft)

    def test_get_report_values(self):
        # Get report data
        model_name = 'report.edi_voxel_account_invoice.template_voxel_invoice'
        report_edi_obj = self.env[model_name]
        report_data = report_edi_obj._get_report_values(self.invoice.ids)
        # Get expected data
        expected_report_data = self._get_invoice_data()
        # Check data
        self.assertDictEqual(report_data, expected_report_data)

    def _get_invoice_data(self):
        return {
            'general': self._get_general_data(),
            'supplier': self._get_suplier_data(),
            'client': self._get_client_data(),
            'customers': self._get_customers_data(),
            'comments': self._get_comments_data(),
            'references': self._get_references_data(),
            'products': self._get_products_data(),
            'taxes': self._get_taxes_data(),
            'tota_summary': self._get_total_summary_data(),
        }

    # report data. Auxiliary methods
    # ------------------------------
    def _get_general_data(self):
        return {
            'Type': 'FacturaComercial',
            'Ref': False,
            'Date': '2019-04-13',
            'Currency': 'USD',
        }

    def _get_suplier_data(self):
        return {
            'CIF': 'US1234567890',
            'Company': 'YourCompany',
            'Address': '1725 Slough Ave., Street 2',
            'City': 'Scranton',
            'PC': '18540',
            'Province': 'Pennsylvania',
            'Country': 'US',
            'Email': 'info@yourcompany.example.com',
        }

    def _get_client_data(self):
        return {
            'SupplierClientID': 'C01',
            'CIF': 'BE0123456789',
            'Company': 'Client (test)',
            'Address': 'Street 1, Street 2',
            'City': 'City (test)',
            'PC': '10000',
            'Province': 'West Virginia',
            'Country': 'USA',
            'Email': 'client_test@example.com',
        }

    def _get_customers_data(self):
        return []

    def _get_comments_data(self):
        return []

    def _get_references_data(self):
        return []

    def _get_products_data(self):
        return [
            {
                'product': {
                    'SupplierSKU': 'DC_001',
                    'CustomerSKU': '1234567891234',
                    'Item': 'Product 1 (test)',
                    'Qty': "2.0",
                    'MU': 'Unidades',
                    'UP': "750.0",
                    'Total': "1500.0",
                },
                'taxes': [],
                'discounts': [],
            },
            {
                'product': {
                    'SupplierSKU': 'DC_002',
                    'CustomerSKU': False,
                    'Item': 'Product 2 (test)',
                    'Qty': "3.0",
                    'MU': 'Unidades',
                    'UP': "147.0",
                    'Total': "441.0",
                },
                'taxes': [
                    {
                        'Rate': "15.0",
                        'Type': False,
                    },
                    {
                        'Rate': "30.0",
                        'Type': False,
                    },
                ],
                'discounts': [{
                    'Amount': "-29.4",
                    'Qualifier': 'Descuento',
                    'Rate': "20.0",
                    'Type': 'Comercial',
                }],
            },
            {
                'product': {
                    'SupplierSKU': 'DC_003',
                    'CustomerSKU': False,
                    'Item': 'Product 3 (test)',
                    'Qty': "0.0",
                    'MU': 'Unidades',
                    'UP': "0.0",
                    'Total': "0.0",
                },
                'taxes': [],
                'discounts': [],
            },
        ]

    def _get_taxes_data(self):
        return [
            {
                'Amount': "52.92",
                'Rate': "15.0",
                'Type': False,
            },
            {
                'Amount': "105.84",
                'Rate': "30.0",
                'Type': False,
            },
        ]

    def _get_total_summary_data(self):
        return {
            'Tax': "158.76",
            'SubTotal': "1852.8",
            'Total': "2011.56",
        }
