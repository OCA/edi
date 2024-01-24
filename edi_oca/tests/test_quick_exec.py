# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

import mock

from .common import EDIBackendCommonComponentRegistryTestCase
from .fake_components import (
    FakeInputProcess,
    FakeOutputChecker,
    FakeOutputGenerator,
    FakeOutputSender,
)

LOGGERS = ("odoo.addons.edi_oca.models.edi_backend", "odoo.addons.queue_job.delay")


class EDIQuickExecTestCase(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_components(
            cls,
            FakeOutputGenerator,
            FakeOutputSender,
            FakeOutputChecker,
            FakeInputProcess,
        )
        cls.partner2 = cls.env.ref("base.res_partner_10")
        cls.partner3 = cls.env.ref("base.res_partner_12")

    def setUp(self):
        super().setUp()
        FakeOutputGenerator.reset_faked()
        FakeOutputSender.reset_faked()
        FakeOutputChecker.reset_faked()
        FakeInputProcess.reset_faked()

    def test_quick_exec_on_create_no_call(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        model = self.env["edi.exchange.record"]
        # quick exec is off, we should not get any call
        with mock.patch.object(type(model), "_execute_next_action") as mocked:
            record0 = self.backend.create_record("test_csv_output", vals)
            mocked.assert_not_called()
            self.assertEqual(record0.edi_exchange_state, "new")
        # enabled but bypassed
        self.exchange_type_out.exchange_file_auto_generate = True
        self.exchange_type_out.quick_exec = True
        with mock.patch.object(type(model), "_execute_next_action") as mocked:
            record0 = self.backend.with_context(
                edi__skip_quick_exec=True
            ).create_record("test_csv_output", vals)
            # quick exec is off, we should not get any call
            mocked.assert_not_called()
            self.assertEqual(record0.edi_exchange_state, "new")

    def test_quick_exec_on_create_out(self):
        self.exchange_type_out.exchange_file_auto_generate = True
        self.exchange_type_out.quick_exec = True
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record0 = self.backend.create_record("test_csv_output", vals)
        # File generated and sent!
        self.assertEqual(record0.edi_exchange_state, "output_sent")
        self.assertTrue(FakeOutputGenerator.check_called_for(record0))
        self.assertEqual(
            record0._get_file_content(), FakeOutputGenerator._call_key(record0)
        )

    def test_quick_exec_on_create_in(self):
        self.exchange_type_in.quick_exec = True
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "exchange_file": base64.b64encode(b"1234"),
            "edi_exchange_state": "input_received",
        }
        record0 = self.backend.create_record("test_csv_input", vals)
        self.assertEqual(record0.edi_exchange_state, "input_processed")
        self.assertTrue(FakeInputProcess.check_called_for(record0))

    def test_quick_exec_on_retry(self):
        self.exchange_type_in.quick_exec = True
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "edi_exchange_state": "input_processed_error",
            "exchange_file": base64.b64encode(b"1234"),
        }
        record0 = self.backend.with_context(edi__skip_quick_exec=True).create_record(
            "test_csv_input", vals
        )
        self.assertEqual(record0.edi_exchange_state, "input_processed_error")
        self.assertTrue(record0.retryable)
        # get record w/ a clean context
        record0 = self.backend.exchange_record_model.browse(record0.id)
        record0.action_retry()
        # The file has been rolled back and processed right away
        self.assertEqual(record0.edi_exchange_state, "input_processed")
        self.assertTrue(FakeInputProcess.check_called_for(record0))
