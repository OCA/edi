# Copyright 2026 teamDSI
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo.tests.common import TransactionCase
from odoo.tools import file_open


class TestUblPriceUnit(TransactionCase):
    """The unit price must reproduce the net amount of the line (BT-131)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")

    def _parse(self, filename):
        f = file_open("account_invoice_import_ubl/tests/files/" + filename, "rb")
        content = f.read()
        f.close()
        return self.env["account.invoice.import"].parse_invoice(
            base64.b64encode(content), filename, self.company
        )

    def test_price_unit_recomputed_when_inconsistent(self):
        parsed = self._parse("UBLInvoice-price-unit.xml")
        lines = parsed["lines"]
        self.assertEqual(len(lines), 3)
        # cbc:PriceAmount is 0.00 while the line carries 154.20: without the
        # fallback the line is imported at zero and doubled by an adjustment
        # line.
        self.assertAlmostEqual(lines[0]["price_unit"], 154.20, places=2)
        # The price is quoted for a base quantity of 100 (BT-149).
        self.assertAlmostEqual(lines[1]["price_unit"], 0.10, places=2)
        # The file is consistent: the price it carries is kept as-is.
        self.assertAlmostEqual(lines[2]["price_unit"], 48.05, places=2)
        # In all three cases the lines add up to the declared BT-106.
        self.assertAlmostEqual(
            sum(line["qty"] * line["price_unit"] for line in lines),
            parsed["amount_untaxed"],
            places=2,
        )
