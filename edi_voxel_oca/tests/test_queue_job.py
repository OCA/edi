# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2025 Guavana - Leonardo J. Caballero G.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestQueueJob(TransactionCase):
    def setUp(self):
        super(TestQueueJob, self).setUp()
        self.queue_job = self.env["queue.job"].create(
            {
                "name": "Test Job",
                "state": "pending",
            }
        )

    def test_voxel_do_now(self):
        self.queue_job.voxel_do_now()
        self.assertFalse(self.queue_job.eta, "ETA should be set to False")

    def test_voxel_cancel_now(self):
        self.queue_job.voxel_cancel_now()
        self.assertFalse(
            self.queue_job.exists(),
            "Job should be unlinked if in pending, enqueued, or failed state",
        )

    def test_voxel_requeue_sudo(self):
        self.queue_job.voxel_requeue_sudo()
        self.assertEqual(self.queue_job.state, "enqueued", "Job should be requeued")
