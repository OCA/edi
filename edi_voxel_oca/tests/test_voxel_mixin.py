# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2025 Guavana - Leonardo J. Caballero G.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestVoxelMixin(TransactionCase):
    def setUp(self):
        super(TestVoxelMixin, self).setUp()
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
                "voxel_enabled": True,
            }
        )
        self.mixin = self.env["voxel.mixin"].create(
            {
                "voxel_state": "not_sent",
                # 'company_id': self.company.id,
            }
        )

    @patch("odoo.addons.edi_voxel_oca.models.voxel_mixin.requests.put")
    def test_send_voxel_report_success(self, mock_put):
        mock_put.return_value.status_code = 200
        self.mixin._send_voxel_report("Outbox", "test.xml", b"<xml></xml>")
        self.assertEqual(self.mixin.voxel_state, "sent", "Voxel state should be 'sent'")

    @patch("odoo.addons.edi_voxel_oca.models.voxel_mixin.requests.put")
    def test_send_voxel_report_failure(self, mock_put):
        mock_put.return_value.status_code = 500
        with self.assertRaises(Exception) as context:
            self.mixin._send_voxel_report("Outbox", "test.xml", b"<xml></xml>")
        self.assertTrue("specific error message" in str(context.exception))
        self.assertEqual(
            self.mixin.voxel_state, "sent_errors", "Voxel state should be 'sent_errors'"
        )

    @patch("odoo.addons.edi_voxel_oca.models.voxel_mixin.requests.get")
    def test_list_voxel_document_filenames(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"test1.xml\ntest2.xml\n"
        filenames = self.mixin._list_voxel_document_filenames("Outbox", self.company)
        self.assertEqual(
            filenames,
            ["test1.xml", "test2.xml"],
            "Filenames should match the expected list",
        )

    @patch("odoo.addons.edi_voxel_oca.models.voxel_mixin.requests.get")
    def test_read_voxel_document(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"<xml></xml>"
        content = self.mixin._read_voxel_document("Inbox", self.company, "test.xml")
        self.assertEqual(
            content, "<xml></xml>", "Content should match the expected XML"
        )

    @patch("odoo.addons.edi_voxel_oca.models.voxel_mixin.requests.delete")
    def test_delete_voxel_document(self, mock_delete):
        mock_delete.return_value.status_code = 200
        self.mixin._delete_voxel_document("Inbox", "test.xml", self.company)
        mock_delete.assert_called_once()

    def test_get_voxel_filename(self):
        self.mixin.get_document_type = MagicMock(return_value="INV")
        filename = self.mixin._get_voxel_filename()
        self.assertTrue(
            filename.startswith("INV_"), "Filename should start with 'INV_'"
        )
        self.assertTrue(filename.endswith(".xml"), "Filename should end with '.xml'")

    def test_cancel_voxel_jobs(self):
        job = self.env["queue.job"].create(
            {
                "name": "Test Job",
                "state": "pending",
            }
        )
        self.mixin.voxel_job_ids = [(4, job.id)]
        self.mixin._cancel_voxel_jobs()
        self.assertEqual(
            self.mixin.voxel_state, "cancelled", "Voxel state should be 'cancelled'"
        )
        self.assertFalse(job.exists(), "Job should be unlinked")
