# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

import mock

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
        cls.record_in = cls.backend.create_record("test_csv_input", vals)
        cls.record_out = cls.backend.create_record("test_csv_output", vals)
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

    def test_01_process_record_in_success(self):
        with self._mock_listener_move_file():
            self.record_in.write({"edi_exchange_state": "input_received"})
            self.record_in.action_exchange_process()
            storage, from_dir_str, to_dir_str, filename = self.fake_move_args
            self.assertEqual(storage, self.backend.storage_id)
            self.assertEqual(from_dir_str, self.backend.input_dir_pending)
            self.assertEqual(to_dir_str, self.backend.input_dir_done)
            self.assertEqual(filename, self.record_in.exchange_filename)

    def test_02_process_record_in_with_error(self):
        with self._mock_listener_move_file():
            self.record_in.write({"edi_exchange_state": "input_received"})
            self.record_in._set_file_content("TEST %d" % self.record_in.id)
            self.record_in.with_context(
                test_break_process="OOPS! Something went wrong :("
            ).action_exchange_process()
            storage, from_dir_str, to_dir_str, filename = self.fake_move_args
            self.assertEqual(storage, self.backend.storage_id)
            self.assertEqual(from_dir_str, self.backend.input_dir_pending)
            self.assertEqual(to_dir_str, self.backend.input_dir_error)
            self.assertEqual(filename, self.record_in.exchange_filename)

    def test_03_process_record_out_success(self):
        with self._mock_listener_move_file():
            self.record_out.write({"edi_exchange_state": "output_pending"})
            self.record_out.action_exchange_send()
            self.record_out._notify_done()
            storage, from_dir_str, to_dir_str, filename = self.fake_move_args
            self.assertEqual(storage, self.backend.storage_id)
            self.assertEqual(from_dir_str, self.backend.output_dir_pending)
            self.assertEqual(to_dir_str, self.backend.output_dir_done)
            self.assertEqual(filename, self.record_out.exchange_filename)

    def test_04_process_record_out_with_error(self):
        with self._mock_listener_move_file():
            self.record_out.write({"edi_exchange_state": "output_pending"})
            self.record_out._set_file_content("TEST %d" % self.record_out.id)
            self.record_out.with_context(
                test_break_process="OOPS! Something went wrong :("
            ).action_exchange_send()
            self.record_out._notify_error("process_ko")
            storage, from_dir_str, to_dir_str, filename = self.fake_move_args
            self.assertEqual(storage, self.backend.storage_id)
            self.assertEqual(from_dir_str, self.backend.output_dir_pending)
            self.assertEqual(to_dir_str, self.backend.output_dir_error)
            self.assertEqual(filename, self.record_out.exchange_filename)
