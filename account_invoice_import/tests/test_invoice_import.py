# Copyright 2017 Akretion
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import unittest.mock
from random import randint

from odoo import Command, fields
from odoo.tests.common import TransactionCase
from odoo.tools import file_open, float_is_zero


class TestInvoiceImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.company.invoice_import_email = "alexis.delattre@testme.com"
        cls.expense_account = cls.env["account.account"].create(
            {
                "code": "612AII",
                "name": "expense account invoice import",
                "account_type": "expense",
                "company_id": cls.company.id,
            }
        )
        cls.income_account = cls.env["account.account"].create(
            {
                "code": "707AII",
                "name": "revenue account invoice import",
                "account_type": "income",
                "company_id": cls.company.id,
            }
        )
        cls.adj_debit_account = cls.env["account.account"].create(
            {
                "code": "658AII",
                "name": "Adjustment debit account",
                "account_type": "expense",
                "company_id": cls.company.id,
            }
        )
        cls.adj_credit_account = cls.env["account.account"].create(
            {
                "code": "758AII",
                "name": "Adjustment credit account",
                "account_type": "income",
                "company_id": cls.company.id,
            }
        )
        cls.company.adjustment_debit_account_id = cls.adj_debit_account.id
        cls.company.adjustment_credit_account_id = cls.adj_credit_account.id
        purchase_tax_vals = {
            "name": "Test 1% VAT",
            "description": "ZZ-VAT-buy-1.0",
            "type_tax_use": "purchase",
            "amount": 1,
            "amount_type": "percent",
            "unece_type_id": cls.env.ref("account_tax_unece.tax_type_vat").id,
            "unece_categ_id": cls.env.ref("account_tax_unece.tax_categ_s").id,
            "company_id": cls.company.id,
        }
        cls.purchase_tax = cls.env["account.tax"].create(purchase_tax_vals)
        sale_tax_vals = purchase_tax_vals.copy()
        sale_tax_vals.update({"description": "ZZ-VAT-sale-1.0", "type_tax_use": "sale"})
        cls.sale_tax = cls.env["account.tax"].create(sale_tax_vals)
        cls.product = (
            cls.env["product.product"]
            .with_company(cls.company.id)
            .create(
                {
                    "name": "Expense product",
                    "default_code": "AII-TEST-PRODUCT",
                    "taxes_id": [(6, 0, [cls.sale_tax.id])],
                    "supplier_taxes_id": [Command.set([cls.purchase_tax.id])],
                    "property_account_income_id": cls.income_account.id,
                    "property_account_expense_id": cls.expense_account.id,
                }
            )
        )
        cls.all_import_config = [
            {
                "single_line": True,
                "account": cls.expense_account,
                "taxes": cls.purchase_tax,
                "company": cls.company,
            },
            {"single_line": False, "product": cls.product, "company": cls.company},
            {
                "account": cls.expense_account,
                "company": cls.company,
            },
            {"product": cls.product, "company": cls.company},
            {"company": cls.company},
        ]

        # Define partners as supplier and customer
        # Wood Corner
        cls.env.ref("base.res_partner_1").supplier_rank = 1
        # Deco Addict
        cls.env.ref("base.res_partner_2").customer_rank = 1
        cls.pur_journal1 = cls.env["account.journal"].create(
            {
                "type": "purchase",
                "code": "XXXP1",
                "name": "Test Purchase Journal 1",
                "sequence": 10,
                "company_id": cls.company.id,
            }
        )
        cls.pur_journal2 = cls.env["account.journal"].create(
            {
                "type": "purchase",
                "code": "XXXP2",
                "name": "Test Purchase Journal 2",
                "sequence": 100,
                "company_id": cls.company.id,
            }
        )
        cls.partner_with_email = cls.env["res.partner"].create(
            {
                "is_company": True,
                "name": "AgroMilk",
                "email": "invoicing@agromilk.com",
                "country_id": cls.env.ref("base.fr").id,
            }
        )
        cls.partner_with_email_with_inv_config = cls.env["res.partner"].create(
            {
                "is_company": True,
                "name": "Anevia",
                "email": "invoicing@anevia.com",
                "country_id": cls.env.ref("base.fr").id,
                "invoice_import_product_id": cls.product.id,
                "invoice_import_label": "Flamingo 220S",
            }
        )

    def test_import_in_invoice(self):
        parsed_inv = {
            "type": "in_invoice",
            "journal": {"code": "XXXP2"},
            "amount_untaxed": 100.0,
            "amount_total": 101.0,
            "date": "2017-08-16",
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
        for import_c in self.all_import_config:
            # hack to have a unique vendor inv ref
            parsed_inv["invoice_number"] = "INV-%s" % randint(100000, 999999)
            inv = self.env["account.invoice.import"].create_invoice(
                parsed_inv, import_c
            )
            self.assertEqual(inv.move_type, parsed_inv["type"])
            self.assertEqual(inv.company_id.id, self.company.id)
            self.assertFalse(
                inv.currency_id.compare_amounts(
                    inv.amount_untaxed, parsed_inv["amount_untaxed"]
                )
            )
            self.assertFalse(
                inv.currency_id.compare_amounts(
                    inv.amount_total, parsed_inv["amount_total"]
                )
            )
            self.assertEqual(
                fields.Date.to_string(inv.invoice_date), parsed_inv["date"]
            )
            self.assertEqual(
                fields.Date.to_string(inv.invoice_date_due), parsed_inv["date_due"]
            )
            self.assertEqual(inv.journal_id.id, self.pur_journal2.id)

    def test_import_in_invoice_with_global_adjustment(self):
        parsed_inv = {
            "type": "in_invoice",
            "journal": {"code": "XXXP2"},
            "invoice_number": "TESTAIIGLOBAL",
            "amount_untaxed": 100.05,
            "amount_total": 101.0,
            "date": "2023-04-08",
            "date_due": "2023-05-07",
            "partner": {"name": "Wood Corner"},
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
        import_config = {"company": self.company}
        inv = self.env["account.invoice.import"].create_invoice(
            parsed_inv, import_config
        )
        self.assertEqual(inv.move_type, parsed_inv["type"])
        self.assertFalse(
            inv.currency_id.compare_amounts(
                inv.amount_untaxed, parsed_inv["amount_untaxed"]
            )
        )
        self.assertFalse(
            inv.currency_id.compare_amounts(
                inv.amount_total, parsed_inv["amount_total"]
            )
        )
        # Check that we have an adjustment line
        self.assertEqual(len(inv.invoice_line_ids), 2)

    def test_import_out_invoice(self):
        parsed_inv = {
            "type": "out_invoice",
            "date": "2017-08-16",
            "partner": {"name": "Deco Addict"},
            "lines": [
                {
                    "product": {"code": "AII-TEST-PRODUCT"},
                    "name": "Super product",
                    "qty": 3,
                    "price_unit": 100,
                    "discount": 10,
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
        for import_config in self.all_import_config:
            if import_config.get("single_line"):
                continue
            inv = self.env["account.invoice.import"].create_invoice(
                parsed_inv, import_config
            )
            self.assertFalse(
                inv.currency_id.compare_amounts(inv.amount_untaxed, 270.00)
            )
            self.assertFalse(inv.currency_id.compare_amounts(inv.amount_total, 272.70))
            self.assertEqual(
                fields.Date.to_string(inv.invoice_date), parsed_inv["date"]
            )

    def test_import_in_invoice_special_display_types(self):
        parsed_inv = {
            "type": "in_invoice",
            "journal": {"code": "XXXP2"},
            "amount_untaxed": 0.0,
            "amount_total": 0.0,
            "date": "2017-08-16",
            "partner": {"name": "Wood Corner"},
            "lines": [
                {"line_note": "This is a line note"},
                {"sectionheader": "SECTION 1"},
            ],
        }
        import_config = {"company": self.company}
        parsed_inv["invoice_number"] = "INV-%s" % randint(100000, 999999)
        inv = self.env["account.invoice.import"].create_invoice(
            parsed_inv, import_config
        )
        # We expect two created invoice lines corresponding to the note and section
        self.assertEqual(len(inv.invoice_line_ids), 2)
        types = [line.display_type for line in inv.invoice_line_ids]
        self.assertIn("line_note", types)
        self.assertIn("line_section", types)
        # Special display lines should not have a product linked
        for line in inv.invoice_line_ids:
            self.assertFalse(line.product_id)

    def test_import_in_invoice_mixed_display_types_with_product(self):
        parsed_inv = {
            "type": "in_invoice",
            "journal": {"code": "XXXP2"},
            "amount_untaxed": 100.0,
            "amount_total": 101.0,
            "date": "2017-08-16",
            "partner": {"name": "Wood Corner"},
            "lines": [
                {"sectionheader": "SECTION 1"},
                {"line_note": "This is a line note"},
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
            ],
        }
        import_config = {"company": self.company}
        parsed_inv["invoice_number"] = "INV-%s" % randint(100000, 999999)
        inv = self.env["account.invoice.import"].create_invoice(
            parsed_inv, import_config
        )
        # Expect three lines: section, note, and product
        self.assertEqual(len(inv.invoice_line_ids), 3)
        types = [line.display_type for line in inv.invoice_line_ids]
        self.assertIn("line_section", types)
        self.assertIn("line_note", types)
        self.assertIn("product", types)
        # Check product line exists and has correct product and qty
        prod_lines = [
            line for line in inv.invoice_line_ids if line.display_type == "product"
        ]
        self.assertEqual(len(prod_lines), 1)
        prod_line = prod_lines[0]
        self.assertEqual(prod_line.product_id.id, self.product.id)
        self.assertEqual(prod_line.quantity, 2)

    _fake_email = """
Received: by someone@example.com
Message-Id: <v0214040cad6a13935723@foo.com>
Mime-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Date: Thursday, 4 Jun 1998 09:43:14 -0800
To: project-discussion@example.com
From: Nina Marton <nina@example.com>
Subject: Happy Birthday

Happy Birthday!
See you this evening,
Nina
"""

    def test_email_gateway(self):
        """No exception occurs on incoming email"""
        self.env["mail.thread"].with_context(
            mail_channel_noautofollow=True
        ).message_process("account.invoice.import", self._fake_email)

    def test_email_gateway_multi_comp_1_matching(self):
        comp = self.env["res.company"].create(
            {
                "name": "Let it fail INC",
                "invoice_import_email": "project-discussion@example.com",
            }
        )
        logger_name = "odoo.addons.account_invoice_import.wizard.account_invoice_import"

        mock_parse = unittest.mock.patch.object(
            type(self.env["mail.thread"]), "message_parse"
        )
        with self.assertLogs(logger_name) as watcher:
            # NOTE: for some reason in tests the msg is not parsed properly
            # and message_dict is kind of empty.
            # Nevertheless, it doesn't really matter
            # because here we want to make sure that the code works as expected
            # when a msg is properly parsed.
            with mock_parse as mocked:
                mocked_msg = {
                    "to": "project-discussion@example.com",
                    "email_from": "Nina Marton <nina@example.com>",
                    "message_id": "<v0214040cad6a13935723@foo.com>",
                    "references": "",
                    "in_reply_to": "",
                    "subject": "Happy Birthday",
                    "recipients": "project-discussion@example.com",
                    "body": self._fake_email,
                    "date": "2022-05-26 10:30:00",
                }
                mocked.return_value = mocked_msg
                self.env["mail.thread"].with_context(
                    mail_channel_noautofollow=True
                ).message_process("account.invoice.import", self._fake_email)
            expected_msgs = (
                f"New email received. "
                f"Date: {mocked_msg['date']}, Message ID: {mocked_msg['message_id']}. "
                f"Executing with user ID {self.env.user.id}",
                f"Matched message {mocked_msg['message_id']}: "
                f"importing invoices in company ID {comp.id}",
                "The email has no attachments, skipped.",
            )
            for msg in expected_msgs:
                self.assertIn(msg, "\n".join(watcher.output))

    def test_email_gateway_multi_comp_none_matching(self):
        self.env["res.company"].create({"name": "Let it fail INC"})
        logger_name = "odoo.addons.account_invoice_import.wizard.account_invoice_import"
        with self.assertLogs(logger_name, "ERROR") as watcher:
            self.env["mail.thread"].with_context(
                mail_channel_noautofollow=True
            ).message_process("account.invoice.import", self._fake_email)
            expected_msg = (
                "Mail gateway in multi-company setup: mail ignored. "
                "No destination found for message_id ="
            )
            self.assertIn(expected_msg, watcher.output[0])

    def prepare_email_with_attachment(self, sender_email):
        file_name = "unknown_invoice.pdf"
        file_path = "account_invoice_import/tests/pdf/%s" % file_name
        with file_open(file_path, "rb") as f:
            pdf_file = f.read()
        msg_dict = {
            "email_from": '"My supplier" <%s>' % sender_email,
            "to": self.company.invoice_import_email,
            "subject": "Invoice n°1242",
            "body": "Please find enclosed your PDF invoice",
            "message_id": "<v0214040cad98743824@foo.com>",
            "attachments": [
                self.env["mail.thread"]._Attachment(file_name, pdf_file, {})
            ],
        }
        return msg_dict

    def test_email_no_partner_match(self):
        sender_email = "invoicing@unknownsupplier.com"
        msg_dict = self.prepare_email_with_attachment(sender_email)
        self.env["account.invoice.import"].message_new(msg_dict)
        move = self.env["account.move"].search(
            [
                ("company_id", "=", self.company.id),
                ("move_type", "=", "in_invoice"),
                ("invoice_source_email", "like", sender_email),
                ("state", "=", "draft"),
            ]
        )
        self.assertEqual(len(move), 1)
        self.assertFalse(move.partner_id)
        self.assertTrue(self.company.currency_id.is_zero(move.amount_total))
        self.assertFalse(move.invoice_date)

    def test_email_partner_no_invoice_config(self):
        sender_email = self.partner_with_email.email
        msg_dict = self.prepare_email_with_attachment(sender_email)
        self.env["account.invoice.import"].message_new(msg_dict)
        move = self.env["account.move"].search(
            [
                ("company_id", "=", self.company.id),
                ("move_type", "=", "in_invoice"),
                ("partner_id", "=", self.partner_with_email.id),
                ("state", "=", "draft"),
            ]
        )
        self.assertEqual(len(move), 1)
        self.assertTrue(self.company.currency_id.is_zero(move.amount_total))
        self.assertFalse(move.invoice_date)

    def test_email_partner_invoice_config(self):
        partner = self.partner_with_email_with_inv_config
        sender_email = partner.email
        msg_dict = self.prepare_email_with_attachment(sender_email)
        self.env["account.invoice.import"].message_new(msg_dict)
        move = self.env["account.move"].search(
            [
                ("company_id", "=", self.company.id),
                ("move_type", "=", "in_invoice"),
                ("partner_id", "=", partner.id),
                ("state", "=", "draft"),
            ]
        )
        self.assertEqual(len(move), 1)
        self.assertTrue(self.company.currency_id.is_zero(move.amount_total))
        self.assertFalse(move.invoice_date)
        self.assertEqual(len(move.invoice_line_ids), 1)
        iline = move.invoice_line_ids
        self.assertEqual(iline.product_id.id, self.product.id)
        self.assertEqual(iline.quantity, 1)
        self.assertEqual(iline.name, partner.invoice_import_label)
        price_prec = self.env["decimal.precision"].precision_get("Product Price")
        self.assertTrue(float_is_zero(iline.price_unit, precision_digits=price_prec))
        self.assertTrue(self.company.currency_id.is_zero(iline.price_subtotal))
