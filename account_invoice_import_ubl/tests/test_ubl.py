# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools import file_open, mute_logger

LOGGER = "odoo.addons.account_invoice_import_ubl.wizard.account_invoice_import"


class TestUbl(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.expense_account = cls.env["account.account"].search(
            [
                ("company_id", "=", cls.company.id),
                ("account_type", "=", "expense"),
            ],
            limit=1,
        )
        cls.purchase_tax = cls.env["account.tax"].search(
            [
                ("company_id", "=", cls.company.id),
                ("type_tax_use", "=", "purchase"),
                ("amount_type", "=", "percent"),
                ("amount", ">", 5),
            ],
            limit=1,
        )
        # When creating a new demo DB, the CoA is installed
        # AFTER account_invoice_import_facturx, so the search= on field account_id
        # in the demo XML file of this module doesn't give any result.
        # That's why we set the account_id field of account.invoice.import.config here
        demo_import_configs = cls.env["account.invoice.import.config"].search(
            [
                ("company_id", "=", cls.company.id),
                ("invoice_line_method", "in", ("1line_no_product", "nline_no_product")),
                ("account_id", "=", False),
            ]
        )
        demo_import_configs.write({"account_id": cls.expense_account.id})
        demo_import_configs = cls.env["account.invoice.import.config"].search(
            [
                ("company_id", "=", cls.company.id),
                ("invoice_line_method", "=", "1line_no_product"),
                ("tax_ids", "=", False),
            ]
        )
        demo_import_configs.write({"tax_ids": [(6, 0, [cls.purchase_tax.id])]})

    @mute_logger(LOGGER, "odoo.models.unlink")
    def test_import_ubl_invoice(self):
        sample_files = {
            "UBLKetentest_Referentiefactuur_20150100.xml": {
                "invoice_number": "20150101",
                "amount_untaxed": 420.0,
                "amount_total": 475.20,
                "invoice_date": "2015-02-16",
                "due_date": "2015-02-16",
                "partner_xmlid": "account_invoice_import_ubl.ketentest",
            },
            "efff_BE0505890632_160421_Inv_16117778.xml": {
                "invoice_number": "16117778",
                "origin": "59137222",
                "amount_untaxed": 31.00,
                "amount_total": 37.51,
                "invoice_date": "2016-04-21",
                "due_date": "2016-04-28",
                "partner_xmlid": "account_invoice_import_ubl.exact_belgium",
            },
            "UBLInvoice-multitankcard-line_adjust.xml": {
                "invoice_number": "6311117",
                "amount_untaxed": 75.01,
                "amount_total": 90.77,
                "invoice_date": "2017-03-07",
                "partner_xmlid": "account_invoice_import_ubl.multi_tank",
            },
        }
        amo = self.env["account.move"]
        aiio = self.env["account.invoice.import"]
        for (sample_file, res_dict) in sample_files.items():
            f = file_open("account_invoice_import_ubl/tests/files/" + sample_file, "rb")
            pdf_file = f.read()
            f.close()
            wiz = aiio.create(
                {
                    "invoice_file": base64.b64encode(pdf_file),
                    "invoice_filename": sample_file,
                }
            )
            wiz.import_invoice()
            invoices = amo.search(
                [
                    ("state", "=", "draft"),
                    ("move_type", "in", ("in_invoice", "in_refund")),
                    ("ref", "=", res_dict["invoice_number"]),
                ]
            )
            self.assertEqual(len(invoices), 1)
            inv = invoices[0]
            self.assertEqual(inv.move_type, res_dict.get("move_type", "in_invoice"))
            str_invoice_date = fields.Date.to_string(inv.invoice_date)
            self.assertEqual(str_invoice_date, res_dict["invoice_date"])
            if res_dict.get("origin"):
                self.assertEqual(inv.invoice_origin, res_dict["origin"])
            if res_dict.get("date_due"):
                self.assertEqual(inv.invoice_date_due, res_dict["date_due"])
            self.assertEqual(inv.partner_id, self.env.ref(res_dict["partner_xmlid"]))
            cur = inv.currency_id
            self.assertEqual(
                cur.compare_amounts(
                    inv.amount_untaxed,
                    res_dict["amount_untaxed"],
                ),
                0,
            )
            self.assertEqual(
                cur.compare_amounts(
                    inv.amount_total,
                    res_dict["amount_total"],
                ),
                0,
            )
            invoices.unlink()
