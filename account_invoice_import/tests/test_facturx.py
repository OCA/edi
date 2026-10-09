# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import Command, fields
from odoo.tests.common import TransactionCase
from odoo.tools import file_open, mute_logger


class TestFacturx(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        adjustment_credit_account_id = (
            cls.env["account.account"]
            .create(
                {
                    "company_ids": [Command.set([cls.company.id])],
                    "code": "758FXADJUST",
                    "name": "Adjustment income account",
                    "account_type": "income",
                }
            )
            .id
        )
        adjustment_debit_account_id = (
            cls.env["account.account"]
            .create(
                {
                    "company_ids": [Command.set([cls.company.id])],
                    "code": "658FXADJUST",
                    "name": "Adjustment expense account",
                    "account_type": "expense",
                }
            )
            .id
        )
        cls.company.write(
            {
                "adjustment_credit_account_id": adjustment_credit_account_id,
                "adjustment_debit_account_id": adjustment_debit_account_id,
            }
        )
        cls.expense_account = cls.env["account.account"].search(
            [
                ("company_ids", "=", cls.company.id),
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
        cls.jolie_boutique_partner = cls.env["res.partner"].create(
            {
                "name": "Ma jolie boutique",
                "is_company": True,
                "country_id": cls.env.ref("base.fr").id,
                "vat": "FR11999999998",
                "invoice_import_shrink_lines": "single",
                "invoice_import_account_id": cls.expense_account.id,
                "invoice_import_tax_ids": [Command.set(cls.purchase_tax.ids)],
            }
        )

    # avoid warning logs pypdf._reader: incorrect startxref pointer(1)
    @mute_logger("pypdf._reader")
    def test_import_facturx_invoice(self):
        sample_files = {
            "Facture_FR_BASICWL.pdf": {
                "invoice_number": "FA-2017-0010",
                "amount_untaxed": 624.90,
                "amount_total": 671.15,
                "invoice_date": "2017-11-13",
                "partner_id": self.jolie_boutique_partner.id,
            },
            "Facture_FR_EN16931.pdf": {
                "invoice_number": "FA-2017-0010",
                "amount_untaxed": 624.90,
                "amount_total": 671.15,
                "invoice_date": "2017-11-13",
                "partner_id": self.jolie_boutique_partner.id,
            },
            "Facture_FR_EXTENDED.pdf": {
                "invoice_number": "FA-2017-0010",
                "amount_untaxed": 624.90,
                "amount_total": 671.15,
                "invoice_date": "2017-11-13",
                "partner_id": self.jolie_boutique_partner.id,
            },
        }
        amo = self.env["account.move"]
        cur = self.env.ref("base.EUR")
        for inv_file, res_dict in sample_files.items():
            f = file_open(
                "account_invoice_import_facturx/tests/files/" + inv_file, "rb"
            )
            pdf_file = f.read()
            f.close()
            wiz = self.env["account.invoice.import"].create(
                {
                    "invoice_attachment_ids": [
                        Command.create({"raw": pdf_file, "name": inv_file})
                    ],
                    "company_id": self.company.id,
                    "debug_disable_company_check": True,
                }
            )
            wiz.import_invoices_button()
            invoices = amo.search(
                [
                    ("state", "=", "draft"),
                    ("move_type", "in", ("in_invoice", "in_refund")),
                    ("ref", "=", res_dict["invoice_number"]),
                    ("company_id", "=", self.company.id),
                ]
            )
            self.assertEqual(len(invoices), 1)
            inv = invoices[0]
            self.assertEqual(inv.move_type, res_dict.get("type", "in_invoice"))
            self.assertEqual(
                fields.Date.to_string(inv.invoice_date), res_dict["invoice_date"]
            )
            if res_dict.get("invoice_date_due"):
                self.assertEqual(
                    fields.Date.to_string(inv.invoice_date_due),
                    res_dict["invoice_date_due"],
                )
            self.assertEqual(
                inv.partner_id.id,
                res_dict["partner_id"],
            )
            self.assertFalse(
                cur.compare_amounts(
                    inv.amount_untaxed,
                    res_dict["amount_untaxed"],
                )
            )
            self.assertFalse(
                cur.compare_amounts(
                    inv.amount_total,
                    res_dict["amount_total"],
                )
            )
            # Delete because several sample invoices have the same number
            invoices.unlink()
