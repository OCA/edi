# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime

from odoo.tests import TransactionCase


class TestVoxelAccountInvoice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        # Invoice line account
        # Invoice company
        cls.main_company = cls.env.ref("base.main_company")
        cls.main_company.write(
            {
                "vat": "US1234567890",
                "street": "Street 1",
                "street2": "Street 2",
                "name": "YourCompany",
                "city": "City",
                "zip": "99999",
                "state_id": cls.env.ref("base.state_es_m").id,
                "country_id": cls.env.ref("base.es").id,
                "email": "info@yourcompany.example.com",
            }
        )
        # Set to false to avoid compare distinct data than expected
        cls.env["ir.config_parameter"].sudo().set_param(
            "account.use_invoice_terms", False
        )
        # Invoice client
        partner = cls.env["res.partner"].create(
            {
                "ref": "C01",
                "vat": "BE0123456789",
                "name": "Client (test)",
                "email": "client_test@example.com",
                "street": "Street 1",
                "street2": "Street 2",
                "city": "City (test)",
                "zip": "10000",
                "state_id": cls.env.ref("base.state_us_49").id,
                "country_id": cls.env.ref("base.us").id,
            }
        )
        # Invoice products
        product_obj = cls.env["product.product"]
        product_1 = product_obj.create(
            {"default_code": "DC_001", "name": "Product 1 (test)"}
        )
        cls.env["product.customerinfo"].create(
            {
                "partner_id": partner.id,
                "product_tmpl_id": product_1.product_tmpl_id.id,
                "product_id": product_1.id,
                "product_code": "1234567891234",
            }
        )
        product_2 = product_obj.create(
            {"default_code": "DC_002", "name": "Product 2 (test)"}
        )
        product_3 = product_obj.create(
            {"default_code": "DC_003", "name": "Product 3 (test)"}
        )
        tax_group_15 = cls.env["account.tax.group"].create({"name": "Tax 15%"})
        tax_group_30 = cls.env["account.tax.group"].create({"name": "Tax 30%"})
        tax_15 = cls.env["account.tax"].create(
            {
                "name": "Tax 15%",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": 15,
                "tax_group_id": tax_group_15.id,
            }
        )
        tax_30 = cls.env["account.tax"].create(
            {
                "name": "Tax 30.00%",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": 30,
                "tax_group_id": tax_group_30.id,
            }
        )
        # Invoice
        cls.invoice = cls.env["account.move"].create(
            {
                "partner_id": partner.id,
                "partner_shipping_id": False,
                "move_type": "out_invoice",
                "currency_id": cls.main_company.currency_id.id,
                "invoice_date": date(2019, 4, 13),
                "company_id": cls.main_company.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product_1.id,
                            "quantity": 2,
                            "price_unit": 750,
                            "tax_ids": False,
                            "name": "Product 1",
                            "product_uom_id": cls.env.ref("uom.product_uom_unit").id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": product_2.id,
                            "quantity": 3,
                            "price_unit": 147,
                            "discount": 20,
                            "tax_ids": [(6, 0, (tax_15 | tax_30).ids)],
                            "name": "Product 2",
                            "product_uom_id": product_2.uom_id.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": product_3.id,
                            "quantity": 0,
                            "price_unit": 0,
                            "tax_ids": False,
                            "name": "Product 3",
                            "product_uom_id": product_3.uom_id.id,
                        },
                    ),
                ],
            }
        )

    def test_get_voxel_filename(self):
        bef = datetime.now()
        bef = datetime(
            bef.year,
            bef.month,
            bef.day,
            bef.hour,
            bef.minute,
            bef.second,
            (bef.microsecond // 1000) * 1000,
        )
        filename = self.invoice._get_voxel_filename()
        document_type, date_time = filename[:-4].split("_", 1)
        date_time = datetime.strptime(date_time, "%Y%m%d_%H%M%S_%f")
        self.assertEqual(document_type, "Factura")
        self.assertGreaterEqual(date_time, bef)

    def test_get_report_values(self):
        # Get report data
        model_name = "report.edi_voxel_account_invoice_oca.template_voxel_invoice"
        report_edi_obj = self.env[model_name]
        report_data = report_edi_obj._get_report_values(self.invoice.ids)
        # Get expected data
        expected_report_data = self._get_invoice_data()
        # Check data
        self.maxDiff = None
        self.assertDictEqual(report_data, expected_report_data)

    def _get_invoice_data(self):
        return {
            "general": self._get_general_data(),
            "supplier": self._get_suplier_data(),
            "client": self._get_client_data(),
            "customers": self._get_customers_data(),
            "comments": self._get_comments_data(),
            "references": self._get_references_data(),
            "products": self._get_products_data(),
            "taxes": self._get_taxes_data(),
            "tota_summary": self._get_total_summary_data(),
        }

    # report data. Auxiliary methods
    # ------------------------------
    def _get_general_data(self):
        return {
            "Type": "FacturaComercial",
            "Ref": "INV/2019/00001",
            "Date": "2019-04-13",
            # Set currency code from company for resilient tests
            "Currency": self.main_company.currency_id.name,
        }

    def _get_suplier_data(self):
        return {
            "CIF": "US1234567890",
            "Company": "YourCompany",
            "Address": "Street 1, Street 2",
            "City": "City",
            "PC": "99999",
            "Province": "Madrid",
            "Country": "ESP",
            "Email": "info@yourcompany.example.com",
        }

    def _get_client_data(self):
        return {
            "SupplierClientID": "C01",
            "CIF": "BE0123456789",
            "Company": "Client (test)",
            "Address": "Street 1, Street 2",
            "City": "City (test)",
            "PC": "10000",
            "Province": "West Virginia",
            "Country": "USA",
            "Email": "client_test@example.com",
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
                "product": {
                    "SupplierSKU": "DC_001",
                    "CustomerSKU": "1234567891234",
                    "Item": "Product 1 (test)",
                    "Qty": "2.0",
                    "MU": "Unidades",
                    "UP": "750.0",
                    "Total": "1500.0",
                },
                "taxes": [],
                "discounts": [],
            },
            {
                "product": {
                    "SupplierSKU": "DC_002",
                    "CustomerSKU": False,
                    "Item": "Product 2 (test)",
                    "Qty": "3.0",
                    "MU": "Unidades",
                    "UP": "147.0",
                    "Total": "352.8",
                },
                "taxes": [
                    {"Rate": "15.0", "Type": False},
                    {"Rate": "30.0", "Type": False},
                ],
                "discounts": [
                    {
                        "Amount": "-29.4",
                        "Qualifier": "Descuento",
                        "Rate": "20.0",
                        "Type": "Comercial",
                    }
                ],
            },
            {
                "product": {
                    "SupplierSKU": "DC_003",
                    "CustomerSKU": False,
                    "Item": "Product 3 (test)",
                    "Qty": "0.0",
                    "MU": "Unidades",
                    "UP": "0.0",
                    "Total": "0.0",
                },
                "taxes": [],
                "discounts": [],
            },
        ]

    def _get_taxes_data(self):
        return [
            {
                "Amount": "52.92",
                "Rate": "15.0",
                "Type": False,
                "Base": "352.8",
                "Description": "Tax 15%",
            },
            {
                "Amount": "105.84",
                "Rate": "30.0",
                "Type": False,
                "Base": "352.8",
                "Description": "Tax 30.00%",
            },
        ]

    def _get_total_summary_data(self):
        return {
            "Tax": "158.76",
            "SubTotal": "1852.8",
            "Total": "2011.56",
        }
