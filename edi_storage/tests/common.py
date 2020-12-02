# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
import functools

import mock

from odoo.addons.edi.tests.common import EDIBackendCommonComponentTestCase

STORAGE_BACKEND_MOCK_PATH = (
    "odoo.addons.storage_backend.models.storage_backend.StorageBackend"
)


class TestEDIStorageBase(EDIBackendCommonComponentTestCase):
    @classmethod
    def _get_backend(cls):
        return cls.env.ref("edi_storage.demo_edi_backend_storage")

    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        cls.filedata = base64.b64encode(b"This is a simple file")
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
            "exchange_file": cls.filedata,
        }
        cls.record = cls.backend.create_record("test_csv_output", vals)

        cls.fakepath = "/tmp/{}".format(cls._filename(cls))
        with open(cls.fakepath, "w+b") as fakefile:
            fakefile.write(b"filecontent")

        cls.fakepath_ack = "/tmp/{}.ack".format(cls._filename(cls))
        with open(cls.fakepath_ack, "w+b") as fakefile:
            fakefile.write(b"ACK filecontent")

        cls.fakepath_error = "/tmp/{}.error".format(cls._filename(cls))
        with open(cls.fakepath_error, "w+b") as fakefile:
            fakefile.write(b"ERROR XYZ: line 2 broken on bla bla")

        cls.checker = cls.backend._find_component(
            ["edi.storage.check"], work_ctx={"exchange_record": cls.record}
        )
        cls.sender = cls.backend._find_component(
            ["edi.storage.send"], work_ctx={"exchange_record": cls.record}
        )

    def setUp(self):
        super().setUp()
        self._storage_backend_calls = []

    def _filename(self, record=None, ack=False):
        record = record or self.record
        if ack:
            record.type_id.ack_type_id._make_exchange_filename(record)
        return record.exchange_filename

    def _file_fullpath(self, state, record=None, ack=False):
        record = record or self.record
        fname = self._filename(record, ack=ack)
        if state == "error-report":
            # Exception as we read from the same path but w/ error suffix
            state = "error"
            fname += ".error"
        return (
            self.checker._remote_file_path(record.direction, state, fname)
        ).as_posix()

    def _mocked_backend_get(self, mocked_paths, path, **kwargs):
        self._storage_backend_calls.append(path)
        if mocked_paths.get(path):
            with open(mocked_paths.get(path), "rb") as remote_file:
                return remote_file.read()
        raise FileNotFoundError()

    def _mocked_backend_add(self, path, data, **kwargs):
        self._storage_backend_calls.append(path)

    def _mock_storage_backend_get(self, mocked_paths):
        mocked = functools.partial(self._mocked_backend_get, mocked_paths)
        return mock.patch(STORAGE_BACKEND_MOCK_PATH + ".get", mocked)

    def _mock_storage_backend_add(self):
        return mock.patch(STORAGE_BACKEND_MOCK_PATH + ".add", self._mocked_backend_add)

    def _test_result(
        self, record, expected_values, expected_messages=None, state_paths=None,
    ):
        state_paths = state_paths or ("done", "pending", "error")
        # Paths will be something like:
        # [
        # 'demo_out/pending/$filename.csv',
        # 'demo_out/pending/$filename.csv',
        # 'demo_out/error/$filename.csv',
        # ]
        for state in state_paths:
            path = self._file_fullpath(state, record=record)
            self.assertIn(path, self._storage_backend_calls)
        self.assertRecordValues(record, [expected_values])
        if expected_messages:
            # consider only edi related messages
            messages = record.record.message_ids.filtered(
                lambda x: "edi-exchange" in x.body
            )
            self.assertEqual(len(messages), len(expected_messages))
            for msg_rec, expected in zip(messages, expected_messages):
                self.assertIn(expected["message"], msg_rec.body)
                self.assertIn("level-" + expected["level"], msg_rec.body)
        # TODO: test content of file sent

    def _test_send(self, record, mocked_paths=None):
        with self._mock_storage_backend_add():
            if mocked_paths:
                with self._mock_storage_backend_get(mocked_paths):
                    self.backend.exchange_send(record)
            else:
                self.backend.exchange_send(record)

    def _test_run_cron(self, mocked_paths):
        with self._mock_storage_backend_add():
            with self._mock_storage_backend_get(mocked_paths):
                self.backend._cron_check_output_exchange_sync()
