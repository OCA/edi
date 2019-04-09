# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from odoo.tests import common


class TestVoxelAccountInvoice(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestVoxelAccountInvoice, cls).setUpClass()

        account_type_revenue = cls.env.ref('account.data_account_type_revenue')
        account_revenue = cls.env['account.account'].search(
            [('user_type_id', '=', account_type_revenue.id)], limit=1)

        main_company = cls.env.ref('base.main_company')
        main_company.write({'vat': 'US1234567890', 'street2': 'Street 2'})

        partner = cls.env.ref("base.res_partner_2")
        partner.write(
            {'vat': 'BE0477472701', 'street2': 'Street 3', 'ref': 'C01'})

        cls.invoice = cls.env['account.invoice'].create({
            'partner_id': partner.id,
            'type': 'out_invoice',
            'currency_id': cls.env.ref('base.USD').id,
            'date_invoice': datetime(2019, 4, 13),
            'company_id': main_company.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': cls.env.ref("product.product_product_4").id,
                    'quantity': 2,
                    'price_unit': 750,
                    'name': 'Product 4',
                    'uom_id': cls.env.ref('product.product_uom_unit').id,
                    'account_id': account_revenue.id,
                }),
                (0, 0, {
                    'product_id': cls.env.ref("product.product_product_5").id,
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
                    'name': 'Product 5',
                    'uom_id': cls.env.ref('product.product_uom_unit').id,
                    'account_id': account_revenue.id,
                })
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
        aft = datetime.now()
        aft = datetime(aft.year, aft.month, aft.day, aft.hour, aft.minute,
                       aft.second, (bef.microsecond // 1000) * 1000)
        self.assertGreaterEqual(date_time, bef)
        self.assertLessEqual(date_time, aft)

    def test_get_report_values(self):
        # Get report data
        model_name = 'report.edi_voxel_account_invoice.template_voxel_invoice'
        report_edi_obj = self.env[model_name]
        report_data = report_edi_obj.get_report_values(self.invoice.ids)
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
            'CIF': 'BE0477472701',
            'Company': 'Agrolait',
            'Address': '69 rue de Namur, Street 3',
            'City': 'Wavre',
            'PC': '1300',
            'Province': False,
            'Country': 'BEL',
            'Email': 'agrolait@yourcompany.example.com',
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
                    'SupplierSKU': 'E-COM01',
                    'Item': 'iPad Retina Display',
                    'Qty': 2.0,
                    'MU': 'Unidades',
                    'UP': 750.0,
                    'Total': 1500.0,
                },
                'taxes': [],
                'discounts': [],
            },
            {
                'product': {
                    'SupplierSKU': 'E-COM06',
                    'Item': 'Custom Computer (kit)',
                    'Qty': 3.0,
                    'MU': 'Unidades',
                    'UP': 147.0,
                    'Total': 441.0,
                },
                'taxes': [
                    {
                        'Rate': 15.0,
                        'Type': False,
                    },
                    {
                        'Rate': 30.0,
                        'Type': False,
                    },
                ],
                'discounts': [{
                    'Amount': -29.4,
                    'Qualifier': 'Descuento',
                    'Rate': 20.0,
                    'Type': 'Comercial',
                }],
            },
        ]

    def _get_taxes_data(self):
        return [
            {
                'Amount': 52.92,
                'Rate': 15.0,
                'Type': False,
            },
            {
                'Amount': 105.84,
                'Rate': 30.0,
                'Type': False,
            },
        ]

    def _get_total_summary_data(self):
        return {
            'Tax': 158.76,
            'SubTotal': 1852.8,
            'Total': 2011.56,
        }
