# Copyright 2015-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import datetime

from mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools import file_open, float_compare


class TestInvoiceImport(TransactionCase):
    def setUp(self):
        super().setUp()
        frtax = self.env["account.tax"].create(
            {
                "name": "French VAT purchase 20.0%",
                "description": "FR-VAT-buy-20.0",
                "amount": 20,
                "amount_type": "percent",
                "type_tax_use": "purchase",
            }
        )
        # Set this tax on Internet access product
        internet_product = self.env.ref(
            "account_invoice_import_invoice2data.internet_access"
        )
        internet_product.supplier_taxes_id = [(6, 0, [frtax.id])]

    def test_import_free_1line_invoice(self):
        # Check for invoice_line_method is set correctly
        free_import_config = self.env.ref(
            "account_invoice_import_invoice2data.free_import_config"
        )
        self.assertEqual(free_import_config.invoice_line_method, "1line_static_product")

        filename = "invoice_free_fiber_201507.pdf"
        f = file_open("account_invoice_import_invoice2data/tests/pdf/" + filename, "rb")
        pdf_file = f.read()
        pdf_file_b64 = base64.b64encode(pdf_file)
        wiz = self.env["account.invoice.import"].create(
            {
                "invoice_file": pdf_file_b64,
                "invoice_filename": filename,
            }
        )
        f.close()
        wiz.import_invoice()
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
                "invoice_file": pdf_file_b64,
                "invoice_filename": "invoice_free_fiber_201507.pdf",
            }
        )
        action = wiz2.import_invoice()
        self.assertEqual(action["res_model"], "account.invoice.import")
        # Choose to update the existing invoice
        wiz2.update_invoice()
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

    @patch(
        "odoo.addons.account_invoice_import_invoice2data.wizard.account_invoice_import.extract_data"  # noqa: B950
    )
    def test_import_gandi_nline_invoice(self, patched):
        patched.return_value = self.mock_extract_data()

        # Check for invoice_line_method is set correctly
        gandi_import_config = self.env.ref(
            "account_invoice_import_invoice2data.gandi_import_config"
        )
        self.assertEqual(
            gandi_import_config.invoice_line_method, "nline_static_product"
        )

        filename = "invoice_gandi_websites_2022030201155.pdf"
        f = file_open("account_invoice_import_invoice2data/tests/pdf/" + filename, "rb")
        pdf_file = f.read()
        pdf_file_b64 = base64.b64encode(pdf_file)
        wiz = self.env["account.invoice.import"].create(
            {
                "invoice_file": pdf_file_b64,
                "invoice_filename": filename,
            }
        )
        f.close()
        wiz.import_invoice()
        # Check result of invoice creation
        invoices = self.env["account.move"].search(
            [
                ("state", "=", "draft"),
                ("move_type", "=", "in_invoice"),
                ("ref", "=", "2022010100001"),
            ]
        )
        self.assertEqual(len(invoices), 1)
        inv = invoices[0]
        self.assertEqual(inv.move_type, "in_invoice")
        self.assertEqual(fields.Date.to_string(inv.invoice_date), "2022-01-01")
        self.assertEqual(
            inv.partner_id, self.env.ref("account_invoice_import_invoice2data.gandi")
        )
        self.assertEqual(inv.journal_id.type, "purchase")
        self.assertEqual(float_compare(inv.amount_total, 109.97, precision_digits=2), 0)
        self.assertEqual(
            float_compare(inv.amount_untaxed, 91.64, precision_digits=2), 0
        )
        self.assertEqual(len(inv.invoice_line_ids), 7)

    def mock_extract_data(self):
        return {
            "issuer": "Gandi",
            "amount": 109.97,
            "amount_untaxed": 91.64,
            "date": datetime.datetime(2022, 1, 1, 0, 0),
            "invoice_number": "2022010100001",
            "vat": "FR81423093459",
            "partner_name": "Gandi",
            "siren": "423 093 459",
            "lines": [
                {"name": "site1.com", "taxes": 20.0, "price_unit": 12.0},
                {"name": "site2.fr", "taxes": 20.0, "price_unit": 13.91},
                {"name": "site3.fr", "taxes": 20.0, "price_unit": 13.91},
                {"name": "site4.com", "taxes": 20.0, "price_unit": 12.0},
                {"price_unit": 12.0},
                {"name": "site6.fr", "price_unit": 13.91},
                {"taxes": 20.0, "price_unit": 13.91},
            ],
            "currency": "EUR",
            "desc": "Invoice from Gandi",
        }
