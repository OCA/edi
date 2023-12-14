# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from unittest.mock import MagicMock, patch

from odoo.tests import tagged

from odoo.addons.account_invoice_export.tests.common import CommonCase
from odoo.addons.queue_job.tests.common import mock_with_delay


@tagged("post_install", "-at_install")
class TestExportAcountInvoiceJob(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @patch("odoo.addons.account_invoice_export.models.account_move.requests")
    def test_invoice_export_job_is_delayed(self, mock_requests):
        """Check export invoice is run as a job."""
        method_name = "_job_export_invoice"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response
        invoice = self.invoice_1.with_context(resend_ebill=True)
        with mock_with_delay() as (delayable_cls, delayable):
            invoice.export_invoice()
            self.assertEqual(delayable_cls.call_count, 1)
            delay_args, delay_kwargs = delayable_cls.call_args
            self.assertEqual(delay_args, (self.invoice_1,))
            method = getattr(delayable, method_name)
            self.assertEqual(method.call_count, 1)
            self.assertEqual(delay_kwargs["description"], "Export eBill to HttpPost")
