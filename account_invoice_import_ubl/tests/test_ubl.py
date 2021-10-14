# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools import file_open, float_compare, mute_logger

LOGGER = "odoo.addons.account_invoice_import_ubl.wizard.account_invoice_import"


class TestUbl(TransactionCase):
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
            precision_rounding = inv.currency_id.rounding
            self.assertEqual(
                float_compare(
                    inv.amount_untaxed,
                    res_dict["amount_untaxed"],
                    precision_rounding=precision_rounding,
                ),
                0,
            )
            self.assertEqual(
                float_compare(
                    inv.amount_total,
                    res_dict["amount_total"],
                    precision_rounding=precision_rounding,
                ),
                0,
            )
            invoices.unlink()
