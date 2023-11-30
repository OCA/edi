# Copyright 2020 ACSONE
# Copyright 2021 Camptocamp
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import mock
from freezegun import freeze_time

from odoo import fields, tools
from odoo.exceptions import UserError

from odoo.addons.queue_job.tests.common import trap_jobs

from .common import EDIBackendCommonComponentRegistryTestCase
from .fake_components import FakeOutputChecker, FakeOutputGenerator, FakeOutputSender


class EDIBackendTestOutputCase(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_components(
            cls,
            FakeOutputGenerator,
            FakeOutputSender,
            FakeOutputChecker,
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
        }
        cls.record = cls.backend.create_record("test_csv_output", vals)

    def setUp(self):
        super().setUp()
        FakeOutputGenerator.reset_faked()
        FakeOutputSender.reset_faked()
        FakeOutputChecker.reset_faked()

    def test_generate_record_output(self):
        self.record.with_context(fake_output="yeah!").action_exchange_generate()
        self.assertEqual(self.record._get_file_content(), "yeah!")

    def test_generate_record_output_pdf(self):
        pdf_content = tools.file_open(
            "result.pdf", subdir="addons/edi_oca/tests", mode="rb"
        ).read()
        self.record.with_context(fake_output=pdf_content).action_exchange_generate()

    def test_send_record(self):
        self.record.write({"edi_exchange_state": "output_pending"})
        self.record._set_file_content("TEST %d" % self.record.id)
        self.assertFalse(self.record.exchanged_on)
        with freeze_time("2020-10-21 10:00:00"):
            self.record.action_exchange_send()
        self.assertTrue(FakeOutputSender.check_called_for(self.record))
        self.assertRecordValues(self.record, [{"edi_exchange_state": "output_sent"}])
        self.assertEqual(
            fields.Datetime.to_string(self.record.exchanged_on), "2020-10-21 10:00:00"
        )

    def test_send_record_with_error(self):
        self.record.write({"edi_exchange_state": "output_pending"})
        self.record._set_file_content("TEST %d" % self.record.id)
        self.assertFalse(self.record.exchanged_on)
        self.record.with_context(
            test_break_send="OOPS! Something went wrong :("
        ).action_exchange_send()
        self.assertTrue(FakeOutputSender.check_called_for(self.record))
        self.assertRecordValues(
            self.record,
            [
                {
                    "edi_exchange_state": "output_error_on_send",
                }
            ],
        )
        self.assertIn("OOPS! Something went wrong :(", self.record.exchange_error)

    def test_send_invalid_direction(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_input", vals)
        with mock.patch.object(type(self.backend), "_exchange_send") as mocked:
            mocked.return_value = "AAA"
            with self.assertRaises(UserError) as err:
                record.action_exchange_send()
            self.assertEqual(
                err.exception.args[0],
                "Record ID=%d is not meant to be sent!" % record.id,
            )
            mocked.assert_not_called()

    def test_send_not_generated_record(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        with mock.patch.object(type(self.backend), "_exchange_send") as mocked:
            mocked.return_value = "AAA"
            with self.assertRaises(UserError) as err:
                record.action_exchange_send()
            self.assertEqual(
                err.exception.args[0], "Record ID=%d has no file to send!" % record.id
            )
            mocked.assert_not_called()


class EDIBackendTestOutputJobsCase(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_components(
            cls,
            FakeOutputGenerator,
            FakeOutputSender,
            FakeOutputChecker,
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
        }
        cls.record = cls.backend.create_record("test_csv_output", vals)
        cls.record.type_id.exchange_file_auto_generate = True

    @classmethod
    def _setup_context(cls):
        # Re-enable jobs
        return dict(super()._setup_context(), test_queue_job_no_delay=False)

    def test_job(self):
        with trap_jobs() as trap:
            self.backend._check_output_exchange_sync(record_ids=self.record.ids)
            trap.assert_jobs_count(2)
            trap.assert_enqueued_job(
                self.record.action_exchange_generate,
            )
            trap.assert_enqueued_job(
                self.record.action_exchange_send, properties=dict(priority=0)
            )
            # No matter how many times we schedule jobs
            self.record.with_delay().action_exchange_generate()
            self.record.with_delay().action_exchange_generate()
            self.record.with_delay().action_exchange_generate()
            # identity key should prevent having new jobs for same record same file
            trap.assert_jobs_count(2)
            # but if we change the content
            self.record._set_file_content("something different")
            # 1st call will schedule another job
            self.record.with_delay().action_exchange_generate()
            # the 2nd one not
            self.record.with_delay().action_exchange_generate()
            trap.assert_jobs_count(3)
            self.record.with_delay().action_exchange_send()
            trap.assert_jobs_count(4)
        # TODO: test input in the same way
