# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from freezegun import freeze_time
from odoo.exceptions import UserError
from odoo.tests.common import at_install, post_install

from .common import EDIBackendCommonComponentRegistryTestCase
from .fake_components import FakeInputProcess


class EDIBackendTestCase(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
            "exchange_file": base64.b64encode(b"1234"),
        }
        cls.record = cls.backend.create_record("test_csv_input", vals)

    def setUp(self):
        super().setUp()
        self._build_components(
            # TODO: test all components lookup
            FakeInputProcess,
        )
        FakeInputProcess.reset_faked()

    @at_install(False)
    @post_install(True)
    def test_process_record(self):
        self.record.write({"edi_exchange_state": "input_received"})
        with freeze_time("2020-10-22 10:00:00"):
            self.record.action_exchange_process()
        self.assertTrue(FakeInputProcess.check_called_for(self.record))
        self.assertEqual(self.record.edi_exchange_state, "input_processed")
        self.assertEqual(self.record.exchanged_on, "2020-10-22 10:00:00")

    @at_install(False)
    @post_install(True)
    def test_process_record_with_error(self):
        self.record.write({"edi_exchange_state": "input_received"})
        self.record._set_file_content("TEST %d" % self.record.id)
        self.record.with_context(
            test_break_process="OOPS! Something went wrong :("
        ).action_exchange_process()
        self.assertTrue(FakeInputProcess.check_called_for(self.record))
        self.assertEqual(self.record.edi_exchange_state, "input_processed_error")
        self.assertEqual(
            self.record.exchange_error, "ValueError('OOPS! Something went wrong :(',)"
        )

    @at_install(False)
    @post_install(True)
    def test_process_no_file_record(self):
        self.record.write({"edi_exchange_state": "input_received"})
        self.record.exchange_file = False
        with self.assertRaises(UserError):
            self.record.action_exchange_process()

    @at_install(False)
    @post_install(True)
    def test_process_outbound_record(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        record._set_file_content("TEST %d" % record.id)
        with self.assertRaises(UserError):
            record.action_exchange_process()

    # TODO: test ack file are processed
