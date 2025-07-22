# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from unittest.mock import patch

from odoo.exceptions import ValidationError

from .common import CommonCase


class TestExportAcountInvoice(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_log_error_in_chatter(self):
        values = {
            "job_id": "13:123:123",
            "send_error": 500,
            "transmit_method_name": "SendMethod",
        }
        self.invoice_1.log_error_sending_invoice(values)
        self.assertEqual(len(self.invoice_1.activity_ids), 1)
        self.assertEqual(
            self.invoice_1.activity_ids[0].activity_type_id, self.send_exception
        )
        # Multiple error only one exception message
        self.invoice_1.log_error_sending_invoice(values)
        self.assertEqual(len(self.invoice_1.activity_ids), 1)
        # At success exception messages are cleared
        self.invoice_1.log_success_sending_invoice()
        self.assertEqual(len(self.invoice_1.activity_ids), 0)

    def test_get_file_description(self):
        res = self.invoice_1._get_file_for_transmission_method()
        self.assertTrue(res["file"])

    def test_get_url(self):
        url = self.invoice_1.transmit_method_id.get_transmission_url()
        self.assertEqual(url, "https://example.com/post")

    def test_get_header(self):
        header = self.invoice_1.transmit_method_id.get_transmission_http_header()
        self.assertTrue("Authorization" in header.keys())

    @patch("odoo.addons.account_invoice_export.models.account_move.requests.post")
    def test_export_invoice_success(self, mock_post):
        """Mark invoice as exported and log success after export."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "Invoice Sent Successfully"
        self.invoice_1.export_invoice()
        self.assertTrue(self.invoice_1.invoice_exported)
        self.assertTrue(self.invoice_1.invoice_export_confirmed)
        last_message = str(self.invoice_1.message_ids[-1].body)
        self.assertIn(
            "<p>Invoice successfuly sent to HttpPost</p>",
            last_message,
        )

    def test_validations_on_server_action(self):
        """Check validation errors during invoice export."""
        self.invoice_2 = self.invoice_1.copy()
        self.invoice_3 = self.invoice_1.copy()
        self.invoice_4 = self.invoice_1.copy()

        # Post only invoice_2 to simulate different states
        self.invoice_2.action_post()

        # Mark invoice_3 as posted and already exported
        self.invoice_3.action_post()
        self.invoice_3.write({"invoice_exported": True})
        invoices = self.invoice_2 + self.invoice_3 + self.invoice_4
        with self.assertRaises(ValidationError):
            server_action = self.env.ref("account_invoice_export.action_send_ebill")
            server_action.with_context(
                active_model="account.move", active_ids=invoices.ids
            ).run()
