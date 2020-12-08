# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.queue_job.tests.common import JobMixin

from .common import EDIBackendCommonTestCase


class EDIBackendTestCase(EDIBackendCommonTestCase, JobMixin):
    @classmethod
    def _setup_context(cls):
        return dict(super()._setup_context(), test_queue_job_no_delay=None)

    def test_output(self):
        job_counter = self.job_counter()
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        self.backend.with_delay().exchange_generate(record)
        created = job_counter.search_created()
        self.assertEqual(len(created), 1)
        self.assertEqual(
            created.name, "Generate output content for given exchange record."
        )
        self.backend.with_delay().exchange_send(record)
        created = job_counter.search_created()
        self.assertEqual(created[0].name, "Send exchange file.")

    def test_input(self):
        job_counter = self.job_counter()
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_input", vals)
        self.backend.with_delay().exchange_receive(record)
        created = job_counter.search_created()
        self.assertEqual(len(created), 1)
        self.assertEqual(created.name, "Retrieve an incoming document.")
        self.backend.with_delay().exchange_process(record)
        created = job_counter.search_created()
        self.assertEqual(created[0].name, "Process an incoming document.")
