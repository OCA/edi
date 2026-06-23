# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestBaseBusinessDocumentImportIban(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bdio = cls.env["business.document.import"]
        cls.partner = cls.env["res.partner"].create(
            {"name": "IBAN Validation Supplier", "is_company": True}
        )

    def test_match_partner_bank_rejects_invalid_iban(self):
        chatter_msg = []
        partner_bank = self.bdio._match_partner_bank(
            self.partner,
            "invalid",
            False,
            chatter_msg,
            create_if_not_found=True,
        )
        self.assertFalse(partner_bank)
        self.assertIn("is not valid", chatter_msg[0])
