# Copyright 2026 teamDSI
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo.tests.common import TransactionCase
from odoo.tools import file_open


class TestUblItemName(TransactionCase):
    """The label of an invoice line must come from BT-153, not BT-154."""

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

    def test_line_name_prefers_item_name(self):
        parsed = self._parse("UBLInvoice-item-name.xml")
        self.assertEqual(len(parsed["lines"]), 3)
        # BT-153 and BT-154 are both present and differ: the item name wins,
        # so that an issuer using the description for an internal identifier
        # does not end up with a UUID as the label of every line.
        self.assertEqual(
            parsed["lines"][0]["name"], "Monthly subscription for instance b2-15"
        )
        # Only BT-154 is present: the historical behaviour is preserved.
        self.assertEqual(parsed["lines"][1]["name"], "Legacy free-form description")
        # Neither is present: the dash fallback is preserved.
        self.assertEqual(parsed["lines"][2]["name"], "-")
