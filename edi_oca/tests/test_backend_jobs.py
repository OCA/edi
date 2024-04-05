# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import mock
from freezegun import freeze_time
from requests.exceptions import ConnectionError as ReqConnectionError

from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.queue_job.tests.common import JobMixin

from .common import EDIBackendCommonTestCase


class EDIBackendTestJobsCase(EDIBackendCommonTestCase, JobMixin):
    @classmethod
    def _setup_context(cls):
        return dict(super()._setup_context(), queue_job__no_delay=None)

    def _get_related_jobs(self, record):
        # Use domain in action to find all related jobs
        record.ensure_one()
        action = record.action_view_related_queue_jobs()
        return self.env["queue.job"].search(action["domain"])

    def test_output(self):
        job_counter = self.job_counter()
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        self.assertEqual(record.edi_exchange_state, "new")
        job = self.backend.with_delay().exchange_generate(record)
        created = job_counter.search_created()
        self.assertEqual(len(created), 1)
        self.assertEqual(
            created.name, "Generate output content for given exchange record."
        )
        # Check related jobs
        self.assertEqual(created, self._get_related_jobs(record))
        with mock.patch.object(
            type(self.backend), "_exchange_generate"
        ) as mocked_generate, mock.patch.object(
            type(self.backend), "_validate_data"
        ) as mocked_validate:
            mocked_generate.return_value = "filecontent"
            mocked_validate.return_value = None
            res = job.perform()
            self.assertEqual(res, "Exchange data generated")
            self.assertEqual(record.edi_exchange_state, "output_pending")
        job = self.backend.with_delay().exchange_send(record)
        created = job_counter.search_created()
        with mock.patch.object(type(self.backend), "_exchange_send") as mocked:
            mocked.return_value = "ok"
            res = job.perform()
            self.assertEqual(res, "Exchange sent")
            self.assertEqual(record.edi_exchange_state, "output_sent")
        self.assertEqual(created[0].name, "Send exchange file.")
        # Check related jobs
        record.invalidate_cache()
        self.assertEqual(created, self._get_related_jobs(record))

    def test_output_fail_retry(self):
        job_counter = self.job_counter()
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "edi_exchange_state": "output_pending",
        }
        record = self.backend.create_record("test_csv_output", vals)
        record._set_file_content("ABC")
        job = self.backend.with_delay().exchange_send(record)
        job_counter.search_created()
        with mock.patch.object(type(self.backend), "_exchange_send") as mocked:
            mocked.side_effect = ReqConnectionError("Connection broken")
            with self.assertRaises(RetryableJobError):
                job.perform()
        self.assertEqual(record.edi_exchange_state, "output_pending")

    def test_output_fail_too_many_retries(self):
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

    def test_input(self):
        job_counter = self.job_counter()
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_input", vals)
        job = self.backend.with_delay().exchange_receive(record)
        created = job_counter.search_created()
        self.assertEqual(len(created), 1)
        self.assertEqual(created.name, "Retrieve an incoming document.")
        # Check related jobs
        self.assertEqual(created, self._get_related_jobs(record))
        with mock.patch.object(
            type(self.backend), "_exchange_receive"
        ) as mocked_receive, mock.patch.object(
            type(self.backend), "_validate_data"
        ) as mocked_validate:
            mocked_receive.return_value = "filecontent"
            mocked_validate.return_value = None
            res = job.perform()
            # the state is not input_pending hence there's nothing to do
            self.assertEqual(res, "Nothing to do. Likely already received.")
            record.edi_exchange_state = "input_pending"
            res = job.perform()
            # the state is not input_pending hence there's nothing to do
            self.assertEqual(res, "Exchange received successfully")
            self.assertEqual(record.edi_exchange_state, "input_received")
        job = self.backend.with_delay().exchange_process(record)
        created = job_counter.search_created()
        self.assertEqual(created[0].name, "Process an incoming document.")

    def test_input_processed_error(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "edi_exchange_state": "input_received",
        }
        record = self.backend.create_record("test_csv_input", vals)
        record._set_file_content("ABC")
        # Process `input_received` records
        job_counter = self.job_counter()
        self.backend._check_input_exchange_sync()
        created = job_counter.search_created()
        # Create job
        self.assertEqual(len(created), 1)
        record.edi_exchange_state = "input_processed_error"
        # Don't re-process `input_processed_error` records
        self.backend._check_input_exchange_sync()
        new_created = job_counter.search_created() - created
        # Should not create new job
        self.assertEqual(len(new_created), 0)
        # Check related jobs
        record.invalidate_cache()
        self.assertEqual(created, self._get_related_jobs(record))
