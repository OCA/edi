# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
from unittest import mock

from odoo.addons.edi_oca.tests.common import EDIBackendCommonComponentRegistryTestCase
from odoo.addons.edi_oca.tests.fake_components import FakeInputProcess

LISTENER_MOCK_PATH = (
    "odoo.addons.edi_storage_oca.components.listener.EdiStorageListener"
)


class EDIBackendTestCase(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._load_module_components(cls, "edi_storage_oca")
        cls._build_components(
            cls,
            FakeInputProcess,
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
            "exchange_file": base64.b64encode(b"1234"),
        }
        cls.record = cls.backend.create_record("test_csv_input", vals)
        cls.fake_move_args = None

    @classmethod
    def _get_backend(cls):
        return cls.env.ref("edi_storage_oca.demo_edi_backend_storage")

    def setUp(self):
        super().setUp()
        FakeInputProcess.reset_faked()

    def _move_file_mocked(self, *args):
        self.fake_move_args = [*args]
        if not all([*args]):
            return False
        return True

    def _mock_listener_move_file(self):
        return mock.patch(LISTENER_MOCK_PATH + "._move_file", self._move_file_mocked)

    def test_01_process_record_success(self):
        with self._mock_listener_move_file():
            self.record.write({"edi_exchange_state": "input_received"})
            self.record.action_exchange_process()
            storage, from_dir_str, to_dir_str, filename = self.fake_move_args
            self.assertEqual(storage, self.backend.storage_id)
            self.assertEqual(from_dir_str, self.backend.input_dir_pending)
            self.assertEqual(to_dir_str, self.backend.input_dir_done)
            self.assertEqual(filename, self.record.exchange_filename)

    def test_02_process_record_with_error(self):
        with self._mock_listener_move_file():
            self.record.write({"edi_exchange_state": "input_received"})
            self.record._set_file_content("TEST %d" % self.record.id)
            self.record.with_context(
                test_break_process="OOPS! Something went wrong :("
            ).action_exchange_process()
            storage, from_dir_str, to_dir_str, filename = self.fake_move_args
            self.assertEqual(storage, self.backend.storage_id)
            self.assertEqual(from_dir_str, self.backend.input_dir_pending)
            self.assertEqual(to_dir_str, self.backend.input_dir_error)
            self.assertEqual(filename, self.record.exchange_filename)
