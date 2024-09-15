# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import HttpCase


class TestEdiPunchout(HttpCase):
    def setUp(self):
        super().setUp()
        self.ids_account = self.env.ref("edi_punchout.edi_punchout_account_ids")
        self.authenticate("demo", "demo")

    def test_get_transaction(self):
        """
        Test we can request a transaction from the UI
        """
        data = self.url_open(
            "/edi_punchout/get_transaction?account_id=%(account_id)s"
            % {"account_id": self.ids_account.id}
        )
        self.assertTrue(
            self.env["edi.punchout.transaction"].search(
                [("transaction_id", "=", data.text)]
            )
        )
