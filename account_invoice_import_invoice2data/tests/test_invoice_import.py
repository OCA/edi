# Copyright 2015-2021 Akretion France (www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
from unittest import mock

from odoo import fields
from odoo.tests.common import SavepointCase
from odoo.tools import file_open, float_compare

# TODO v16: use
# from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT
DISABLED_MAIL_CONTEXT = {
    "tracking_disable": True,
    "mail_create_nolog": True,
    "mail_create_nosubscribe": True,
    "mail_notrack": True,
    "no_reset_password": True,
}


class TestInvoiceImport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        frtax = cls.env["account.tax"].create(
            {
                "name": "French VAT purchase 20.0%",
                "description": "FR-VAT-buy-20.0",
                "amount": 20,
                "amount_type": "percent",
                "type_tax_use": "purchase",
            }
        )
        # Set this tax on Internet access product
        internet_product = cls.env.ref(
            "account_invoice_import_invoice2data.internet_access"
        )
        internet_product.supplier_taxes_id = [(6, 0, [frtax.id])]

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

    def test_import_azure_interior_invoice(self):
        """Function for testing almost all supported fields"""
        filename = "AzureInterior.pdf"
        invoice_file = file_open(
            "account_invoice_import_invoice2data/tests/pdf/" + filename, "rb"
        )
        pdf_file = invoice_file.read()
        pdf_file_b64 = base64.b64encode(pdf_file)
        wiz = self.env["account.invoice.import"].create(
            {
                "invoice_file": pdf_file_b64,
                "invoice_filename": filename,
            }
        )
        invoice_file.close()
        wiz.import_invoice()
        # create_invoice_action_button
        wiz.create_invoice_action(origin="BOSD Import Vendor Bill wizard")
        # Check result of invoice creation
        invoices = self.env["account.move"].search(
            [
                ("state", "=", "draft"),
                # ("move_type", "=", "in_invoice"),
                # ("ref", "=", "INV/2023/03/0008"),
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

        self.assertEqual(
            inv.narration,
            "Due to global inflation our payment term has changed to 15 days.",
        )

        # Following tests are disabled. Not yet implemented in account_invoice_import
        # self.assertEqual(inv.journal_id.payment_reference, "202309097001")
        # self.assertEqual(inv.journal_id.incoterm_id, self.env.ref("account.incoterm_DPU")

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
