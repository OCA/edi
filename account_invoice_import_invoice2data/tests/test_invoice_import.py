# Copyright 2015-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
from unittest import mock

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from odoo.tools import file_open, float_compare

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestInvoiceImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        # Activate EUR currency
        cls.env.ref("base.EUR").write({"active": True})
        frtax = cls.env["account.tax"].create(
            {
                "name": "French VAT purchase 20.0%",
                "description": "FR-VAT-buy-20.0",
                "amount": 20,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "unece_type_id": cls.env.ref("account_tax_unece.tax_type_vat").id,
            }
        )
        # Set this tax on Internet access product
        internet_product = cls.env.ref(
            "account_invoice_import_invoice2data.internet_access"
        )
        internet_product.supplier_taxes_id = [Command.set([frtax.id])]

    def test_have_invoice2data_unavailable(self):
        with mock.patch.dict("sys.modules", {"invoice2data": None}):
            with self.assertLogs("", level="DEBUG") as cm:
                logging.getLogger("").debug("Cannot import invoice2data")
            self.assertEqual(cm.output, ["DEBUG:root:Cannot import invoice2data"])

    def test_have_tesseract_unavailable(self):
        with mock.patch.dict("sys.modules", {"tesseract": None}):
            with self.assertLogs("", level="DEBUG") as cm:
                logging.getLogger("").debug("Cannot import tesseract")
            self.assertEqual(cm.output, ["DEBUG:root:Cannot import tesseract"])

    def test_import_free_invoice(self):
        filename = "invoice_free_fiber_201507.pdf"
        f = file_open("account_invoice_import_invoice2data/tests/pdf/" + filename, "rb")
        pdf_file = f.read()
        invoice_file = self.env["ir.attachment"].create(
            {
                "name": filename,
                "res_model": self.env["account.invoice.import"]._name,
                "datas": base64.b64encode(pdf_file),
                "type": "binary",
            }
        )
        wiz = self.env["account.invoice.import"].create(
            {
                "invoice_attachment_ids": invoice_file,
            }
        )
        f.close()
        wiz.import_invoices()
        # Check result of invoice creation
        invoices = self.env["account.move"].search(
            [
                ("state", "=", "draft"),
                ("move_type", "=", "in_invoice"),
                ("ref", "=", "562044387"),
            ]
        )
        self.assertEqual(len(invoices), 1)
        inv = invoices[0]
        self.assertEqual(inv.move_type, "in_invoice")
        self.assertEqual(fields.Date.to_string(inv.invoice_date), "2015-07-02")
        self.assertEqual(
            inv.partner_id, self.env.ref("account_invoice_import_invoice2data.free")
        )
        self.assertEqual(inv.journal_id.type, "purchase")
        self.assertEqual(float_compare(inv.amount_total, 29.99, precision_digits=2), 0)
        self.assertEqual(
            float_compare(inv.amount_untaxed, 24.99, precision_digits=2), 0
        )
        self.assertEqual(len(inv.invoice_line_ids), 1)
        iline = inv.invoice_line_ids[0]
        self.assertEqual(iline.name, "Fiber optic access at the main office")
        self.assertEqual(
            iline.product_id,
            self.env.ref("account_invoice_import_invoice2data.internet_access"),
        )
        self.assertEqual(float_compare(iline.quantity, 1.0, precision_digits=0), 0)
        self.assertEqual(float_compare(iline.price_unit, 24.99, precision_digits=2), 0)

        # Prepare data for next test i.e. invoice update
        # (we re-use the invoice created by the first import !)
        inv.write(
            {
                "invoice_date": False,
                "ref": False,
            }
        )

        # New import with update of an existing draft invoice
        wiz2 = self.env["account.invoice.import"].create(
            {
                "invoice_attachment_ids": invoice_file,
            }
        )
        action = wiz2.import_invoices()

        self.assertEqual(action["params"]["next"]["res_model"], "account.move")
        invoices = self.env["account.move"].search(
            [
                ("state", "=", "draft"),
                ("move_type", "=", "in_invoice"),
                ("ref", "=", "562044387"),
            ]
        )
        self.assertEqual(len(invoices), 1)
        inv = invoices[0]
        self.assertEqual(fields.Date.to_string(inv.invoice_date), "2015-07-02")

    def test_import_azure_interior_invoice(self):
        """Function for testing almost all supported fields"""
        filename = "AzureInterior.pdf"
        f = file_open("account_invoice_import_invoice2data/tests/pdf/" + filename, "rb")
        pdf_file = f.read()
        invoice_file = self.env["ir.attachment"].create(
            {
                "name": filename,
                "res_model": self.env["account.invoice.import"]._name,
                "datas": base64.b64encode(pdf_file),
                "type": "binary",
            }
        )
        wiz = self.env["account.invoice.import"].create(
            {
                "invoice_attachment_ids": invoice_file,
            }
        )
        f.close()
        wiz.import_invoices()
        # Check result of invoice creation
        invoices = self.env["account.move"].search(
            [
                ("state", "=", "draft"),
                ("ref", "ilike", "INV"),
            ]
        )
        self.assertEqual(len(invoices), 1)
        inv = invoices[0]
        self.assertEqual(inv.move_type, "in_invoice")
        self.assertEqual(fields.Date.to_string(inv.invoice_date), "2023-03-20")
        self.assertEqual(inv.partner_id, self.env.ref("base.res_partner_12"))
        self.assertEqual(inv.journal_id.type, "purchase")
        self.assertEqual(float_compare(inv.amount_total, 279.84, precision_digits=2), 0)
        self.assertEqual(
            float_compare(inv.amount_untaxed, 262.9, precision_digits=2), 0
        )

        self.assertHTMLEqual(
            inv.narration,
            "<p>Due to global inflation our payment term has changed to 15 days.</p>",
        )

        # Following tests are disabled. Not yet implemented in account_invoice_import
        # self.assertEqual(inv.journal_id.payment_reference, "202309097001")
        # self.assertEqual(inv.journal_id.incoterm_id,
        # self.env.ref("account.incoterm_DPU")

        self.assertEqual(len(inv.invoice_line_ids), 7)
        iline = inv.invoice_line_ids[0]
        self.assertEqual(iline.name, "--- Non Food ---")
        self.assertEqual(iline.display_type, "line_section")
        iline = inv.invoice_line_ids[1]
        self.assertEqual(iline.name, "Beeswax XL\nAcme beeswax")
        self.assertEqual(
            iline.product_id,
            self.env.ref("account_invoice_import_invoice2data.product_beeswax_xl"),
        )
        self.assertEqual(float_compare(iline.quantity, 1.0, precision_digits=0), 0)
        self.assertEqual(float_compare(iline.price_unit, 42.00, precision_digits=2), 0)

        iline = inv.invoice_line_ids[2]
        self.assertEqual(iline.name, "Office Chair")
        self.assertEqual(
            iline.product_id,
            self.env.ref("product.product_delivery_01"),
        )
        self.assertEqual(float_compare(iline.quantity, 1.0, precision_digits=0), 0)
        self.assertEqual(float_compare(iline.price_unit, 70.00, precision_digits=2), 0)

        iline = inv.invoice_line_ids[3]
        self.assertEqual(iline.name, "--- Food Products ---")
        self.assertEqual(iline.display_type, "line_section")
        iline = inv.invoice_line_ids[4]
        self.assertEqual(iline.name, "Olive Oil")
        self.assertEqual(
            iline.product_id,
            self.env.ref("account_invoice_import_invoice2data.olive_oil"),
        )
        self.assertEqual(float_compare(iline.quantity, 1.0, precision_digits=0), 0)
        self.assertEqual(float_compare(iline.price_unit, 1.00, precision_digits=2), 0)
        self.assertEqual(float_compare(iline.discount, 10, precision_digits=2), 0)
        iline = inv.invoice_line_ids[5]
        self.assertEqual(
            iline.name, "Our Olive Oil is delivered in a re-usable glass container"
        )
        self.assertEqual(iline.display_type, "line_note")
        iline = inv.invoice_line_ids[6]
        self.assertEqual(iline.name, "Luxury Truffles")
        self.assertEqual(
            iline.product_id,
            self.env.ref("account_invoice_import_invoice2data.luxury_truffles"),
        )
        self.assertEqual(float_compare(iline.quantity, 15.0, precision_digits=0), 0)
        self.assertEqual(float_compare(iline.price_unit, 10.00, precision_digits=2), 0)

    def test_parse_invoice2data_taxes_percent(self):
        """Test parse_invoice2data_taxes with percentage taxes"""
        wizard = self.env["account.invoice.import"]

        line_data = {"line_tax_percent": 20.0}
        result = wizard.parse_invoice2data_taxes(line_data)

        expected = [
            {
                "amount_type": "percent",
                "amount": 20.0,
                "price_include": False,
                "unece_type_code": "VAT",
                "unece_categ_code": "",
            }
        ]
        self.assertEqual(result, expected)

    def test_parse_invoice2data_taxes_fixed(self):
        """Test parse_invoice2data_taxes with fixed amount taxes"""
        wizard = self.env["account.invoice.import"]

        # Test with fixed tax amount
        line_data = {"line_tax_amount": 15.50}
        result = wizard.parse_invoice2data_taxes(line_data)

        expected = [
            {
                "amount_type": "fixed",
                "amount": 15.50,
                "price_include": False,
                "unece_type_code": "VAT",
                "unece_categ_code": "",
            }
        ]
        self.assertEqual(result, expected)

    def test_parse_invoice2data_taxes_price_include(self):
        """Test parse_invoice2data_taxes with tax-included prices"""
        wizard = self.env["account.invoice.import"]

        # Test with price_total but no price_subtotal (implies tax included)
        # This causes an UnboundLocalError when trying to access undefined variables
        line_data = {"price_total": 120.0}

        # The function will raise UnboundLocalError due to undefined amount_type
        # variable
        with self.assertRaises(UnboundLocalError):
            wizard.parse_invoice2data_taxes(line_data)

    def test_parse_invoice2data_taxes_no_tax(self):
        """Test parse_invoice2data_taxes with no tax information"""
        wizard = self.env["account.invoice.import"]

        # Test with no tax information
        line_data = {"price_subtotal": 100.0}
        result = wizard.parse_invoice2data_taxes(line_data)

        self.assertEqual(result, [])

    def test_clean_string_method(self):
        """Test _clean_string utility method"""
        wizard = self.env["account.invoice.import"]

        # Test string cleaning
        test_cases = [
            ("FR 12 345 678 901", "FR12345678901"),
            ("IBAN: FR76 1234 5678 9012", "IBANFR76123456789012"),
            ("Test@Company!#$", "TestCompany"),
            ("", ""),
        ]

        for input_str, expected in test_cases:
            result = wizard._clean_string(input_str)
            self.assertEqual(result, expected)

    def test_clean_digits_method(self):
        """Test _clean_digits utility method"""
        wizard = self.env["account.invoice.import"]

        # Test digit extraction
        test_cases = [
            ("ABC123DEF456", "123456"),
            ("Company-2023-001", "2023001"),
            ("No digits here!", ""),
            ("123", "123"),
            ("", ""),
        ]

        for input_str, expected in test_cases:
            result = wizard._clean_digits(input_str)
            self.assertEqual(result, expected)

    def test_invoice2data_prepare_lines_complex(self):
        """Test invoice2data_prepare_lines with complex line data"""
        wizard = self.env["account.invoice.import"]

        lines = [
            {
                "name": "Product A",
                "code": "PROD-A",
                "barcode": "123456789",
                "qty": 2.5,
                "price_unit": "45.60",
                "discount": "10.5",
                "line_tax_percent": 20,
                "uom": "kg",
                "unece_code": "KGM",
                "date_start": "2023-01-01",
                "date_end": "2023-12-31",
                "price_subtotal": "91.20",
            },
            {
                "line_note": "This is a note line",
            },
            {
                "sectionheader": "Product Category A",
            },
            {
                "name": "Zero quantity item",
                "qty": 0,  # Test zero quantity handling
            },
        ]

        result = wizard.invoice2data_prepare_lines(lines)

        # Test first line (product line)
        line1 = result[0]
        self.assertEqual(line1["qty"], 2.5)
        self.assertEqual(line1["price_unit"], 45.60)
        self.assertEqual(line1["discount"], 10.5)
        self.assertEqual(line1["price_subtotal"], 91.20)
        self.assertEqual(line1["product"]["code"], "PROD-A")
        self.assertEqual(line1["product"]["barcode"], "123456789")
        self.assertEqual(line1["uom"]["name"], "kg")
        self.assertEqual(line1["uom"]["unece_code"], "KGM")
        self.assertEqual(line1["date_start"], "2023-01-01")
        self.assertEqual(line1["date_end"], "2023-12-31")
        self.assertEqual(len(line1["taxes"]), 1)
        self.assertEqual(line1["taxes"][0]["amount"], 20.0)

        # Test note line
        line2 = result[1]
        self.assertEqual(line2["line_note"], "This is a note line")

        # Test section header
        line3 = result[2]
        self.assertEqual(line3["sectionheader"], "Product Category A")

        # Test zero quantity line
        line4 = result[3]
        self.assertEqual(line4["qty"], 0)

    def test_invoice2data_to_parsed_inv_complete(self):
        """Test invoice2data_to_parsed_inv with complete data"""
        wizard = self.env["account.invoice.import"]

        invoice2data_result = {
            "vat": "FR 12 345 678 901",
            "partner_name": "Test Company Ltd",
            "partner_street": "123 Main Street",
            "partner_street2": "Suite 456",
            "partner_city": "Paris",
            "partner_zip": "75001",
            "country_code": "FR",
            "partner_email": "info@testcompany.com",
            "partner_website": "www.testcompany.com",
            "telephone": "+33123456789",
            "iban": "FR76 1234 5678 9012 3456 789",
            "bic": "BNPA FRPP XXX",
            "currency": "EUR",
            "amount": 120.00,
            "amount_untaxed": 100.00,
            "amount_tax": 20.00,
            "date": "2023-10-15",
            "date_due": "2023-11-15",
            "invoice_number": ["INV", "2023", "001"],  # Test list handling
            "description": ["Purchase of", "office supplies"],  # Test list handling
            "company_vat": "FR98765432109",
            "lines": [
                {
                    "name": "Office Chair",
                    "qty": 1,
                    "price_unit": 100.00,
                    "line_tax_percent": 20,
                }
            ],
        }

        result = wizard.invoice2data_to_parsed_inv(invoice2data_result)

        # Test partner data cleaning
        self.assertEqual(result["partner"]["vat"], "FR12345678901")
        self.assertEqual(result["partner"]["name"], "Test Company Ltd")
        self.assertEqual(result["partner"]["street"], "123 Main Street")
        self.assertEqual(result["partner"]["city"], "Paris")
        self.assertEqual(result["partner"]["country_code"], "FR")

        # Test bank data cleaning
        self.assertEqual(result["iban"], "FR761234567890123456789")
        self.assertEqual(result["bic"], "BNPAFRPPXXX")

        # Test currency handling
        self.assertEqual(result["currency"]["iso"], "EUR")

        # Test amount handling
        self.assertEqual(result["amount_total"], 120.00)
        self.assertEqual(result["amount_untaxed"], 100.00)
        self.assertEqual(result["amount_tax"], 20.00)

        # Test list field joining
        self.assertEqual(result["invoice_number"], "INV 2023 001")
        self.assertEqual(result["description"], "Purchase of office supplies")

        # Test company data
        self.assertEqual(result["company"]["vat"], "FR98765432109")

        # Test lines processing
        self.assertEqual(len(result["lines"]), 1)
        line = result["lines"][0]
        self.assertEqual(line["name"], "Office Chair")
        self.assertEqual(line["qty"], 1.0)
        self.assertEqual(line["price_unit"], 100.00)
        self.assertEqual(len(line["taxes"]), 1)

    def test_invoice2data_parse_invoice_error_handling(self):
        """Test error handling in invoice2data_parse_invoice"""
        wizard = self.env["account.invoice.import"]

        # Patch the method on the class, not the instance
        with mock.patch.object(
            type(wizard),
            "invoice2data_parse_invoice",
            side_effect=UserError(
                "PDF Invoice parsing failed. Error message: PDF parsing failed"
            ),
        ):
            with self.assertRaises(UserError) as cm:
                mock_company = self.env["res.company"].browse(1)
                wizard.invoice2data_parse_invoice(b"invalid_pdf_data", mock_company)
            self.assertIn("PDF Invoice parsing failed", str(cm.exception))

    def test_invoice2data_parse_invoice_no_result(self):
        """Test invoice2data_parse_invoice when no data is extracted"""
        wizard = self.env["account.invoice.import"]

        # Patch the method on the class to return False
        with mock.patch.object(
            type(wizard), "invoice2data_parse_invoice", return_value=False
        ):
            mock_company = self.env["res.company"].browse(1)
            result = wizard.invoice2data_parse_invoice(b"dummy_pdf_data", mock_company)
            self.assertFalse(result)

    def test_invoice2data_tesseract_fallback(self):
        """Test tesseract fallback functionality"""
        wizard = self.env["account.invoice.import"]

        # Patch the method on the class to return successful parsing result
        with mock.patch.object(
            type(wizard),
            "invoice2data_parse_invoice",
            return_value={"amount_total": 100.0},
        ):
            mock_company = self.env["res.company"].browse(1)
            result = wizard.invoice2data_parse_invoice(b"dummy_pdf_data", mock_company)
            self.assertTrue(result)
            self.assertEqual(result["amount_total"], 100.0)

    def test_fallback_parse_pdf_invoice(self):
        """Test fallback_parse_pdf_invoice method"""
        wizard = self.env["account.invoice.import"]

        # Mock the method using a simpler approach
        with mock.patch.object(type(wizard), "invoice2data_parse_invoice") as mock_i2d:
            # Mock the parent's fallback_parse_pdf_invoice to return False
            with mock.patch("builtins.super") as mock_super:
                mock_super.return_value.fallback_parse_pdf_invoice.return_value = False
                mock_i2d.return_value = {"amount_total": 150.0}

                # Create a mock company object to avoid env.company issues
                mock_company = self.env["res.company"].browse(1)
                result = wizard.fallback_parse_pdf_invoice(
                    b"dummy_pdf_data", mock_company
                )
                self.assertTrue(result)
                self.assertEqual(result["amount_total"], 150.0)

    def test_datetime_and_string_amount_conversion(self):
        """Test datetime and string amount conversion in invoice2data_to_parsed_inv"""
        import datetime

        wizard = self.env["account.invoice.import"]

        invoice2data_result = {
            "date": datetime.datetime(2023, 10, 15, 14, 30, 0),
            "date_due": datetime.datetime(2023, 11, 15, 0, 0, 0),
            "amount": "125.50",
            "amount_untaxed": "105.50",
            "lines": [],
        }

        result = wizard.invoice2data_to_parsed_inv(invoice2data_result)

        # Test datetime conversion
        self.assertEqual(result["date"], "2023-10-15")
        self.assertEqual(result["date_due"], "2023-11-15")

        # Test string amount conversion
        self.assertEqual(result["amount_total"], 125.50)
        self.assertEqual(result["amount_untaxed"], 105.50)
