# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

import mock
from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError

from .common import EDIBackendCommonComponentRegistryTestCase
from .fake_components import FakeInputProcess

# from odoo.tools import mute_logger


class EDIBackendTestCase(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_components(
            # TODO: test all components lookup
            cls,
            FakeInputProcess,
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
            "exchange_file": base64.b64encode(b"1234"),
        }
        cls.record = cls.backend.create_record("test_csv_input", vals)

    def setUp(self):
        super().setUp()
        FakeInputProcess.reset_faked()

    def test_process_record(self):
        self.record.write({"edi_exchange_state": "input_received"})
        with freeze_time("2020-10-22 10:00:00"):
            self.record.action_exchange_process()
        self.assertTrue(FakeInputProcess.check_called_for(self.record))
        self.assertRecordValues(
            self.record, [{"edi_exchange_state": "input_processed"}]
        )
        self.assertEqual(
            fields.Datetime.to_string(self.record.exchanged_on), "2020-10-22 10:00:00"
        )

    def test_process_record_with_error(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "edi_exchange_state": "input_received",
            "exchange_file": base64.b64encode(b"1234"),
        }
        record = self.backend.create_record("test_csv_input", vals)
        self.backend.exchange_process(record)
        self.assertEqual(record.edi_exchange_state, "input_processed_error")

    def test_process_no_file_record(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "edi_exchange_state": "input_received",
        }
        record = self.backend.create_record("test_csv_input", vals)
        with mock.patch.object(type(self.backend), "_exchange_process") as patch:
            patch.return_value = "AAA"
            with self.assertRaises(UserError):
                self.backend.exchange_process(record)
            patch.assert_not_called()

    def test_process_outbound_record(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        with mock.patch.object(type(self.backend), "_exchange_process") as patch:
            patch.return_value = "AAA"
            with self.assertRaises(UserError):
                self.backend.exchange_process(record)
            patch.assert_not_called()
