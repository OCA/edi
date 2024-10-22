# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

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
        url = self.transmit_method.get_transmission_url()
        self.assertEqual(url, "https://example.com/post")

    def test_get_header(self):
        header = self.transmit_method.get_transmission_http_header()
        self.assertTrue("Authorization" in header.keys())
