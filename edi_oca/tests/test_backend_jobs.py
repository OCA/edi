# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# from odoo.addons.queue_job.tests.common import JobMixin

from .common import EDIBackendCommonTestCase


# class EDIBackendTestCase(EDIBackendCommonTestCase, JobMixin):
class EDIBackendTestCase(EDIBackendCommonTestCase):
    @classmethod
    def _setup_context(cls):
        return dict(super()._setup_context(), test_queue_job_no_delay=None)

    def test_output(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        self.existing = self.env["queue.job"].search([])
        self.backend.with_delay().exchange_generate(record)
        created = self.env["queue.job"].search([]) - self.existing
        self.assertEqual(len(created), 1)
        self.assertEqual(
            created.name, "Generate output content for given exchange record."
        )
        self.existing = self.env["queue.job"].search([])
        self.backend.with_delay().exchange_send(record)
        created = self.env["queue.job"].search([]) - self.existing
        self.assertEqual(created[0].name, "Send exchange file.")

    def test_input(self):
        self.existing = self.env["queue.job"].search([])
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_input", vals)
        self.existing = self.env["queue.job"].search([])
        self.backend.with_delay().exchange_receive(record)
        created = self.env["queue.job"].search([]) - self.existing
        self.assertEqual(len(created), 1)
        self.assertEqual(created.name, "Retrieve an incoming document.")
        self.existing = self.env["queue.job"].search([])
        self.backend.with_delay().exchange_process(record)
        created = self.env["queue.job"].search([]) - self.existing
        self.assertEqual(created[0].name, "Process an incoming document.")
