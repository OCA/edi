import mock
from freezegun import freeze_time
from requests.exceptions import ConnectionError as ReqConnectionError

from odoo.addons.edi_oca.tests.common import EDIBackendCommonTestCase
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.queue_job.tests.common import JobMixin


class EdiExchangeSendingWarning(EDIBackendCommonTestCase, JobMixin):
    @classmethod
    def _setup_context(cls):
        return dict(super()._setup_context(), test_queue_job_no_delay=None)

    def test_output_sending_warning(self):
        job_counter = self.job_counter()
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "edi_exchange_state": "output_pending",
        }
        record = self.backend.create_record("test_csv_output", vals)
        record._write({"create_date": "2024-01-10 09:00:00"})
        record._set_file_content("ABC")
        with mock.patch.object(type(self.backend), "_exchange_send") as mocked:
            mocked.side_effect = ReqConnectionError("Connection broken")
            with freeze_time("2024-01-10 11:00:00"):
                # + 2 hours
                job = self.backend.with_delay().exchange_send(record)
                with self.assertRaises(RetryableJobError):
                    job.perform()
            with freeze_time("2024-01-11 08:50:00"):
                # + 23 hours and 50 minutes
                job = self.backend.with_delay().exchange_send(record)
                with self.assertRaises(RetryableJobError):
                    job.perform()
            self.assertEqual(record.edi_exchange_state, "output_pending")
            with freeze_time("2024-01-11 09:20:00"):
                # + 24 hours and 20 minutes
                job = self.backend.with_delay().exchange_send(record)
                res = job.perform()
            self.assertIn("Error", res)
        job_counter.search_created()
        self.assertEqual(record.edi_exchange_state, "output_error_on_send")
        self.assertEqual(record.sending_error_type, "edi_message_not_sent")
        self.assertEqual(record.transmission_error, True)
        self.assertEqual(
            record.edi_exchange_record_id.edi_exchange_state, "output_error_on_send"
        )
