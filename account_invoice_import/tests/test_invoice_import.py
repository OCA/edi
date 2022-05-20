# Copyright 2017 Akretion
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import mock
from odoo import fields
from odoo.tests.common import SavepointCase
from odoo.tools import float_compare


class TestInvoiceImport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.expense_account = cls.env["account.account"].create(
            {
                "code": "612AII",
                "name": "expense account invoice import",
                "user_type_id": cls.env.ref("account.data_account_type_expenses").id,
                "company_id": cls.company.id,
            }
        )
        cls.income_account = cls.env["account.account"].create(
            {
                "code": "707AII",
                "name": "revenue account invoice import",
                "user_type_id": cls.env.ref("account.data_account_type_revenue").id,
                "company_id": cls.company.id,
            }
        )
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
        cls.product = cls.env["product.product"].create(
            {
                "name": "Expense product",
                "default_code": "AII-TEST-PRODUCT",
                "taxes_id": [(6, 0, [cls.sale_tax.id])],
                "supplier_taxes_id": [(6, 0, [cls.purchase_tax.id])],
                "property_account_income_id": cls.income_account.id,
                "property_account_expense_id": cls.expense_account.id,
            }
        )
        cls.all_import_config = [
            {
                "invoice_line_method": "1line_no_product",
                "account": cls.expense_account,
                "taxes": cls.purchase_tax,
            },
            {"invoice_line_method": "1line_static_product", "product": cls.product},
            {
                "invoice_line_method": "nline_no_product",
                "account": cls.expense_account,
            },
            {"invoice_line_method": "nline_static_product", "product": cls.product},
            {"invoice_line_method": "nline_auto_product"},
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
            parsed_inv["invoice_number"] = "INV-%s" % import_c["invoice_line_method"]
            inv = (
                self.env["account.invoice.import"]
                .with_company(self.company.id)
                .create_invoice(parsed_inv, import_c)
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
        for import_config in self.all_import_config:
            if not import_config["invoice_line_method"].startswith("nline"):
                continue
            inv = (
                self.env["account.invoice.import"]
                .with_company(self.company.id)
                .create_invoice(parsed_inv, import_config)
            )
            prec = inv.currency_id.rounding
            self.assertFalse(inv.currency_id.compare_amounts(inv.amount_untaxed, 30.66))
            self.assertFalse(inv.currency_id.compare_amounts(inv.amount_total, 30.97))
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

        mock_parse = mock.patch.object(type(self.env["mail.thread"]), "message_parse")
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
