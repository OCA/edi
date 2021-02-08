# Copyright 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tools import float_compare

from odoo.addons.base_sparse_field.models.fields import Serialized
from odoo.addons.edi.tests.common import EDIBackendCommonComponentRegistryTestCase

# pytest compatibility
fields.Serialized = Serialized


class TestInvoiceImport(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        cls._load_module_components(cls, "base_business_document_import")
        cls._load_module_components(cls, "account_invoice_import")
        self = cls
        self.expense_account = self.env["account.account"].create(
            {
                "code": "612AII",
                "name": "expense account invoice import",
                "user_type_id": self.env.ref("account.data_account_type_expenses").id,
            }
        )
        self.income_account = self.env["account.account"].create(
            {
                "code": "707AII",
                "name": "revenue account invoice import",
                "user_type_id": self.env.ref("account.data_account_type_revenue").id,
            }
        )
        purchase_tax_vals = {
            "name": "Test 1% VAT",
            "description": "ZZ-VAT-buy-1.0",
            "type_tax_use": "purchase",
            "amount": 1,
            "amount_type": "percent",
            "unece_type_id": self.env.ref("account_tax_unece.tax_type_vat").id,
            "unece_categ_id": self.env.ref("account_tax_unece.tax_categ_s").id,
            # TODO tax armageddon
            # "account_id": self.expense_account.id,
            # "refund_account_id": self.expense_account.id,
        }
        self.purchase_tax = self.env["account.tax"].create(purchase_tax_vals)
        sale_tax_vals = purchase_tax_vals.copy()
        sale_tax_vals.update({"description": "ZZ-VAT-sale-1.0", "type_tax_use": "sale"})
        self.sale_tax = self.env["account.tax"].create(sale_tax_vals)
        self.product_01 = self.env["product.product"].create(
            {
                "name": "Expense product",
                "default_code": "AII-TEST-PRODUCT",
                "taxes_id": [(6, 0, [self.sale_tax.id])],
                "supplier_taxes_id": [(6, 0, [self.purchase_tax.id])],
                "property_account_income_id": self.income_account.id,
                "property_account_expense_id": self.expense_account.id,
            }
        )
        self.product_02 = self.env["product.product"].create(
            {
                "name": "Expense product",
                "default_code": "AII-TEST-PRODUCT-02",
                "taxes_id": [(6, 0, [self.sale_tax.id])],
                "supplier_taxes_id": [(6, 0, [self.purchase_tax.id])],
                "property_account_income_id": self.income_account.id,
                "property_account_expense_id": self.expense_account.id,
            }
        )
        self.product_03 = self.env["product.product"].create(
            {
                "name": "Expense product",
                "default_code": "AII-TEST-PRODUCT-03",
                "taxes_id": [(6, 0, [self.sale_tax.id])],
                "supplier_taxes_id": [(6, 0, [self.purchase_tax.id])],
                "property_account_income_id": self.income_account.id,
                "property_account_expense_id": self.expense_account.id,
            }
        )

        # Define partners as supplier and customer
        # Wood Corner
        self.env.ref("base.res_partner_1").supplier_rank = 1
        # Deco Addict
        self.env.ref("base.res_partner_2").customer_rank = 1
        self.all_import_config = [
            {
                "invoice_line_method": "1line_no_product",
                "account_id": self.expense_account.id,
                "tax_ids": [(6, 0, self.purchase_tax.ids)],
            },
            {
                "invoice_line_method": "1line_static_product",
                "static_product_id": self.product_01.id,
            },
            {
                "invoice_line_method": "nline_no_product",
                "account_id": self.expense_account.id,
            },
            {
                "invoice_line_method": "nline_static_product",
                "static_product_id": self.product_01.id,
            },
            {"invoice_line_method": "nline_auto_product"},
        ]
        self.all_import_config_01 = (
            self.env["account.invoice.import.config"]
            .with_context(
                default_partner_id=self.env.ref("base.res_partner_1").id,
                default_name="Demo configuration",
            )
            .create(self.all_import_config)
        )
        self.all_import_config_02 = (
            self.env["account.invoice.import.config"]
            .with_context(
                default_partner_id=self.env.ref("base.res_partner_2").id,
                default_name="Demo configuration",
            )
            .create(self.all_import_config)
        )

    def test_import_in_invoice(self):
        parsed_inv = {
            "type": "in_invoice",
            "amount_untaxed": 100.0,
            "amount_total": 101.0,
            "invoice_number": "INV-2017-9876",
            "date_invoice": "2017-08-16",
            "date_due": "2017-08-31",
            "date_start": "2017-08-01",
            "date_end": "2017-08-31",
            "partner": {"name": "Wood Corner"},
            "description": "New hi-tech gadget",
            "lines": [
                {
                    "product": {"code": "AII-TEST-PRODUCT"},
                    "name": "Super test product",
                    "qty": 2,
                    "price_unit": 50,
                    "taxes": [
                        {
                            "amount_type": "percent",
                            "amount": 1.0,
                            "unece_type_code": "VAT",
                            "unece_categ_code": "S",
                        }
                    ],
                }
            ],
        }
        for import_config in self.all_import_config_01:
            wizard = self.env["account.invoice.import"].create(
                {"import_config_id": import_config.id, "invoice_file": b"1234"}
            )
            invoice = wizard.create_invoice(parsed_inv)
            invoice.refresh()
            self.assertTrue(invoice.exchange_record_ids)

    def test_import_in_invoice_tax_include(self):
        self.purchase_tax.price_include = True
        parsed_inv = {
            "type": "in_invoice",
            "amount_total": 101.0,
            "invoice_number": "INV-2017-9876",
            "date_invoice": "2017-08-16",
            "date_due": "2017-08-31",
            "date_start": "2017-08-01",
            "date_end": "2017-08-31",
            "partner": {"name": "Wood Corner"},
            "description": "New hi-tech gadget",
            "lines": [
                {
                    "product": {"code": "AII-TEST-PRODUCT"},
                    "name": "Super test product",
                    "qty": 2,
                    "price_unit": 50,
                    "taxes": [
                        {
                            "amount_type": "percent",
                            "amount": 1.0,
                            "unece_type_code": "VAT",
                            "unece_categ_code": "S",
                        }
                    ],
                }
            ],
        }
        for import_config in self.all_import_config_01:
            wizard = self.env["account.invoice.import"].create(
                {"import_config_id": import_config.id, "invoice_file": b"1234"}
            )
            invoice = wizard.create_invoice(parsed_inv)
            invoice.refresh()
            self.assertTrue(invoice.exchange_record_ids)

    def test_update_in_invoice(self):
        parsed_inv = {
            "type": "in_invoice",
            "amount_untaxed": 200.0,
            "amount_total": 202.0,
            "invoice_number": "INV-2017-9876",
            "date_invoice": "2017-08-16",
            "date_due": "2017-08-31",
            "date_start": "2017-08-01",
            "date_end": "2017-08-31",
            "partner": {"name": "Wood Corner"},
            "description": "New hi-tech gadget",
            "lines": [
                {
                    "product": {"code": "AII-TEST-PRODUCT"},
                    "name": "Super test product",
                    "qty": 2,
                    "price_unit": 50,
                    "taxes": [
                        {
                            "amount_type": "percent",
                            "amount": 1.0,
                            "unece_type_code": "VAT",
                            "unece_categ_code": "S",
                        }
                    ],
                },
                {
                    "product": {"code": "AII-TEST-PRODUCT-02"},
                    "name": "Super test product",
                    "qty": 2,
                    "price_unit": 50,
                    "taxes": [
                        {
                            "amount_type": "percent",
                            "amount": 1.0,
                            "unece_type_code": "VAT",
                            "unece_categ_code": "S",
                        }
                    ],
                },
            ],
        }
        move_vals = {
            "type": "in_invoice",
            "partner_id": self.env.ref("base.res_partner_1").id,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product_02.id,
                        "account_id": self.product_02.property_account_income_id.id,
                        "quantity": 1,
                        "product_uom_id": self.product_02.uom_id.id,
                        "tax_ids": [(4, self.purchase_tax.id)],
                        "price_unit": 10,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "product_id": self.product_03.id,
                        "account_id": self.product_03.property_account_income_id.id,
                        "quantity": 1,
                        "product_uom_id": self.product_03.uom_id.id,
                        "tax_ids": [(4, self.purchase_tax.id)],
                        "price_unit": 10,
                    },
                ),
            ],
        }
        for import_config in self.all_import_config_01.filtered(
            lambda r: r.invoice_line_method == "nline_auto_product"
        ):
            move = self.env["account.move"].create(move_vals)
            wizard = self.env["account.invoice.import"].create(
                {
                    "invoice_id": move.id,
                    "import_config_id": import_config.id,
                    "invoice_file": b"1234",
                    "state": "update",
                    "partner_id": move.partner_id.id,
                }
            )
            wizard._update_invoice(parsed_inv)
            move.refresh()
            self.assertTrue(move.exchange_record_ids)

    def test_import_out_invoice(self):
        parsed_inv = {
            "type": "out_invoice",
            "date_invoice": "2017-08-16",
            "partner": {"name": "Deco Addict"},
            "lines": [
                {
                    "product": {"code": "AII-TEST-PRODUCT"},
                    "name": "Super product",
                    "qty": 3,
                    "price_unit": 10.22,
                    "date_start": "2017-08-01",
                    "date_end": "2017-08-31",
                    "taxes": [
                        {  # only needed for method 'nline_no_product'
                            "amount_type": "percent",
                            "amount": 1.0,
                            "unece_type_code": "VAT",
                            "unece_categ_code": "S",
                        }
                    ],
                }
            ],
        }
        for import_config in self.all_import_config_02:
            if not import_config.invoice_line_method.startswith("nline"):
                continue

            wizard = self.env["account.invoice.import"].create(
                {"import_config_id": import_config.id, "invoice_file": b"1234"}
            )
            inv = wizard.create_invoice(parsed_inv)
            prec = inv.currency_id.rounding
            self.assertFalse(
                float_compare(inv.amount_untaxed, 30.66, precision_rounding=prec)
            )
            self.assertFalse(
                float_compare(inv.amount_total, 30.97, precision_rounding=prec)
            )
            inv.refresh()
            self.assertTrue(inv.exchange_record_ids)
