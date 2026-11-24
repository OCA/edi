# Copyright 2026 teamDSI
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64

from odoo.tests.common import TransactionCase
from odoo.tools import file_open

SAMPLE = "Facture_FR_EN16931_line_allowance.xml"


class TestFacturxLineAllowance(TransactionCase):
    """A line level allowance is already deducted from BT-131.

    It must not be counted a second time, whatever the sign the issuer uses
    for ram:ActualAmount.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")

    def test_line_allowance_not_counted_twice(self):
        f = file_open("account_invoice_import_facturx/tests/files/" + SAMPLE, "rb")
        content = f.read()
        f.close()
        parsed = self.env["account.invoice.import"].parse_invoice(
            base64.b64encode(content), SAMPLE, self.company
        )
        lines = parsed["lines"]
        # 3 product lines plus the allowance carried by the first one.
        self.assertEqual(len(lines), 4)
        # The first line is billed 20 x 4.10 = 82.00 with a 2.00 allowance, so
        # ram:LineTotalAmount is 80.00. The product line must carry the gross
        # amount, otherwise the allowance is deducted a second time.
        self.assertAlmostEqual(lines[0]["qty"], 20.0, places=2)
        self.assertAlmostEqual(lines[0]["price_unit"], 4.10, places=2)
        self.assertAlmostEqual(lines[0]["price_subtotal"], 82.00, places=2)
        # The issuer writes the allowance as a negative ram:ActualAmount while
        # BT-136 is defined as a positive amount, the direction being carried
        # by ram:ChargeIndicator. Taking it as-is turns the allowance into a
        # charge.
        self.assertEqual(lines[1]["product"]["code"], "EDI-ALLOWANCE")
        self.assertAlmostEqual(lines[1]["price_unit"], 2.00, places=2)
        self.assertAlmostEqual(lines[1]["price_subtotal"], -2.00, places=2)
        # The lines must add up to BT-106, otherwise _post_process_invoice()
        # makes up the difference with an adjustment line.
        self.assertAlmostEqual(
            sum(line["price_subtotal"] for line in lines),
            parsed["amount_untaxed"],
            places=2,
        )
        self.assertAlmostEqual(parsed["amount_untaxed"], 623.00, places=2)
        self.assertAlmostEqual(parsed["amount_total"], 668.87, places=2)
