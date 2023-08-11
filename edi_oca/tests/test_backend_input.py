# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from .common import EDIBackendCommonComponentRegistryTestCase
from .fake_components import FakeInputReceive


class EDIBackendTestInputCase(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_components(
            # TODO: test all components lookup
            cls,
            FakeInputReceive,
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
        }
        cls.record = cls.backend.create_record("test_csv_input", vals)

    @classmethod
    def _setup_context(cls):
        return dict(
            super()._setup_context(),
            _edi_receive_break_on_error=True,
            _edi_process_break_on_error=True,
        )

    def setUp(self):
        super().setUp()
        FakeInputReceive.reset_faked()

    def test_receive_record_nothing_todo(self):
        self.backend.with_context(fake_output="yeah!").exchange_receive(self.record)
        self.assertEqual(self.record._get_file_content(), "")
        self.assertRecordValues(self.record, [{"edi_exchange_state": "new"}])

    def test_receive_record(self):
        self.record.edi_exchange_state = "input_pending"
        self.backend.with_context(fake_output="yeah!").exchange_receive(self.record)
        self.assertEqual(self.record._get_file_content(), "yeah!")
        self.assertRecordValues(self.record, [{"edi_exchange_state": "input_received"}])
