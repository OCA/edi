# Copyright 2017 Akretion
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import unittest.mock
from random import randint

from odoo import Command, fields
from odoo.exceptions import UserError
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
            # TODO tax armageddon
            # "account_id": cls.expense_account.id,
            # "refund_account_id": cls.expense_account.id,
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

    def test_res_company_cannot_refund_vat(self):
        """Test _cannot_refund_vat method"""
        # Test company with purchase taxes - should return False
        self.assertFalse(self.company._cannot_refund_vat())

        # Create company without purchase taxes - should return True
        company_no_vat = self.env["res.company"].create(
            {
                "name": "No VAT Company",
            }
        )
        self.assertTrue(company_no_vat._cannot_refund_vat())

    def test_res_partner_convert_to_import_config(self):
        """Test _convert_to_import_config method"""
        partner = self.partner_with_email_with_inv_config

        # Test with product configuration
        config = partner._convert_to_import_config(self.company)
        self.assertEqual(config["company"], self.company)
        self.assertEqual(config["product"], partner.invoice_import_product_id)
        self.assertEqual(config["label"], partner.invoice_import_label)
        self.assertFalse(config["single_line"])

        # Test with account and tax configuration
        partner_account_config = self.env["res.partner"].create(
            {
                "name": "Account Config Partner",
                "invoice_import_account_id": self.expense_account.id,
                "invoice_import_tax_ids": [(6, 0, [self.purchase_tax.id])],
                "invoice_import_single_line": True,
            }
        )
        config = partner_account_config._convert_to_import_config(self.company)
        self.assertEqual(config["account"], self.expense_account)
        self.assertEqual(config["taxes"], self.purchase_tax)
        self.assertTrue(config["single_line"])

    def test_res_partner_update_imported_invoice(self):
        """Test update_imported_invoice method"""
        # Create a draft invoice without partner
        invoice = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "company_id": self.company.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Test line",
                            "quantity": 1,
                            "price_unit": 100,
                            "account_id": self.expense_account.id,
                        }
                    )
                ],
            }
        )

        # Create partner linked to this invoice
        partner = self.env["res.partner"].create(
            {
                "name": "Test Supplier",
                "is_company": True,
                "supplier_rank": 1,
                "invoice_import_move_id": invoice.id,
            }
        )

        # Test update
        action = partner.update_imported_invoice()

        # Verify partner was set on invoice
        self.assertEqual(invoice.partner_id, partner)
        self.assertFalse(partner.invoice_import_move_id)
        self.assertEqual(action["res_id"], invoice.id)

    def test_account_move_set_partner_and_update_lines(self):
        """Test _invoice_import_set_partner_and_update_lines method"""
        # Create fiscal position with account and tax mapping
        fp = self.env["account.fiscal.position"].create(
            {
                "name": "Test Fiscal Position",
                "company_id": self.company.id,
            }
        )

        # Create alternative account and tax for mapping
        alt_account = self.env["account.account"].create(
            {
                "code": "612ALT",
                "name": "Alternative expense account",
                "account_type": "expense",
                "company_id": self.company.id,
            }
        )
        alt_tax = self.env["account.tax"].create(
            {
                "name": "Alternative VAT",
                "description": "ALT-VAT-buy-5.0",
                "type_tax_use": "purchase",
                "amount": 5,
                "amount_type": "percent",
                "company_id": self.company.id,
            }
        )

        # Add mappings to fiscal position
        fp.write(
            {
                "account_ids": [
                    Command.create(
                        {
                            "account_src_id": self.expense_account.id,
                            "account_dest_id": alt_account.id,
                        }
                    )
                ],
                "tax_ids": [
                    Command.create(
                        {
                            "tax_src_id": self.purchase_tax.id,
                            "tax_dest_id": alt_tax.id,
                        }
                    )
                ],
            }
        )

        # Create partner with fiscal position
        partner = self.env["res.partner"].create(
            {
                "name": "FP Partner",
                "property_account_position_id": fp.id,
            }
        )

        # Create invoice without partner
        invoice = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "company_id": self.company.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Test line",
                            "quantity": 1,
                            "price_unit": 100,
                            "account_id": self.expense_account.id,
                            "tax_ids": [Command.set([self.purchase_tax.id])],
                        }
                    )
                ],
            }
        )

        # Test the method
        invoice._invoice_import_set_partner_and_update_lines(partner)

        # Verify partner was set and fiscal position applied
        self.assertEqual(invoice.partner_id, partner)
        self.assertEqual(invoice.fiscal_position_id, fp)

        # Verify line was updated with mapped account and tax
        line = invoice.invoice_line_ids.filtered(lambda x: x.display_type == "product")
        self.assertEqual(line.account_id, alt_account)
        self.assertEqual(line.tax_ids, alt_tax)

    def test_parse_invoice_xml_format(self):
        """Test XML invoice parsing"""
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <Invoice>
            <InvoiceNumber>TEST-XML-001</InvoiceNumber>
            <TotalAmount>120.00</TotalAmount>
        </Invoice>"""

        # Test with unsupported XML format (should raise UserError)
        import_wizard = self.env["account.invoice.import"]
        with self.assertRaises(UserError):
            import_wizard.parse_invoice(
                base64.b64encode(xml_content), "test_invoice.xml", self.company
            )

    def test_parse_invoice_invalid_xml(self):
        """Test parsing invalid XML"""
        invalid_xml = b"<Invalid>XML</unclosed>"

        import_wizard = self.env["account.invoice.import"]
        with self.assertRaises(UserError):
            import_wizard.parse_invoice(
                base64.b64encode(invalid_xml), "invalid.xml", self.company
            )

    def test_create_invoice_with_currency(self):
        """Test invoice creation with currency"""
        # Use existing EUR currency from base module
        eur_currency = self.env.ref("base.EUR")

        parsed_inv = {
            "type": "in_invoice",
            "amount_untaxed": 100.0,
            "amount_total": 120.0,
            "date": "2023-10-01",
            "currency": {"iso": "EUR"},
            "partner": {"name": "Test Partner"},
            "lines": [
                {
                    "name": "Test Line",
                    "qty": 1,
                    "price_unit": 100,
                }
            ],
        }

        import_config = {"company": self.company}
        invoice = self.env["account.invoice.import"].create_invoice(
            parsed_inv, import_config
        )

        self.assertEqual(invoice.currency_id, eur_currency)

    def test_invoice_already_exists(self):
        """Test duplicate invoice detection"""
        # Create an existing invoice
        existing_inv = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.env.ref("base.res_partner_1").id,
                "company_id": self.company.id,
                "ref": "DUPLICATE-001",
            }
        )

        parsed_inv = {
            "type": "in_invoice",
            "invoice_number": "DUPLICATE-001",
        }

        import_wizard = self.env["account.invoice.import"]
        result = import_wizard._invoice_already_exists(
            parsed_inv, existing_inv.commercial_partner_id, self.company.id
        )

        self.assertEqual(result, existing_inv)

    def test_adjustment_line_creation(self):
        """Test adjustment line creation for rounding differences"""
        parsed_inv = {
            "type": "in_invoice",
            "amount_untaxed": 100.01,  # Slight difference to trigger adjustment
            "amount_total": 120.01,
            "lines": [
                {
                    "name": "Test Line",
                    "qty": 1,
                    "price_unit": 100,
                    "price_subtotal": 100.01,
                }
            ],
        }

        import_config = {"company": self.company}
        invoice = self.env["account.invoice.import"].create_invoice(
            parsed_inv, import_config
        )

        # Should have main line + adjustment line
        self.assertGreater(len(invoice.invoice_line_ids), 1)
        adjustment_lines = invoice.invoice_line_ids.filtered(
            lambda line: "Adjustment" in line.name
        )
        self.assertTrue(adjustment_lines)

    def test_partner_bank_matching(self):
        """Test partner bank account matching and creation"""
        partner = self.env.ref("base.res_partner_1")

        parsed_inv = {
            "type": "in_invoice",
            "amount_total": 100.0,
            "iban": "FR1420041010050500013M02606",
            "bic": "CCBPFRPPVER",
            "partner": {"recordset": partner},
        }

        # Enable auto bank account creation
        self.company.invoice_import_create_bank_account = True

        import_config = {"company": self.company}
        invoice = self.env["account.invoice.import"].create_invoice(
            parsed_inv, import_config
        )

        self.assertTrue(invoice.partner_bank_id)
        # Bank account stores IBAN with spaces, so check without spaces
        self.assertEqual(
            invoice.partner_bank_id.acc_number.replace(" ", ""), parsed_inv["iban"]
        )

    def test_line_with_uom_and_product(self):
        """Test invoice line creation with UOM and product matching"""
        # Use Units UOM which is compatible with the default product UOM category
        uom_unit = self.env.ref("uom.product_uom_unit")

        parsed_inv = {
            "type": "in_invoice",
            "amount_total": 250.0,
            "lines": [
                {
                    "product": {"code": "AII-TEST-PRODUCT"},
                    "name": "Product with UOM",
                    "qty": 5,
                    "price_unit": 50,
                    "uom": {"name": "Units"},
                }
            ],
        }

        import_config = {"company": self.company}
        invoice = self.env["account.invoice.import"].create_invoice(
            parsed_inv, import_config
        )

        line = invoice.invoice_line_ids.filtered(lambda x: x.display_type == "product")
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.product_uom_id, uom_unit)
