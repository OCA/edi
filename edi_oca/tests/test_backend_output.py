# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import mock
from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError

from .common import EDIBackendCommonComponentRegistryTestCase
from .fake_components import FakeOutputChecker, FakeOutputGenerator, FakeOutputSender


class EDIBackendTestCase(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_components(
            # TODO: test all components lookup
            cls,
            FakeOutputGenerator,
            FakeOutputSender,
            FakeOutputChecker,
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
        }
        cls.record = cls.backend.create_record("test_csv_output", vals)

    def setUp(self):
        super().setUp()
        FakeOutputGenerator.reset_faked()
        FakeOutputSender.reset_faked()
        FakeOutputChecker.reset_faked()

    def test_generate_record_output(self):
        self.backend.with_context(fake_output="yeah!").exchange_generate(self.record)
        self.assertEqual(self.record._get_file_content(), "yeah!")

    def test_send_record(self):
        self.record.write({"edi_exchange_state": "output_pending"})
        self.record._set_file_content("TEST %d" % self.record.id)
        self.assertFalse(self.record.exchanged_on)
        with freeze_time("2020-10-21 10:00:00"):
            self.record.action_exchange_send()
        self.assertTrue(FakeOutputSender.check_called_for(self.record))
        self.assertRecordValues(self.record, [{"edi_exchange_state": "output_sent"}])
        self.assertEqual(
            fields.Datetime.to_string(self.record.exchanged_on), "2020-10-21 10:00:00"
        )

    def test_send_record_with_error(self):
        self.record.write({"edi_exchange_state": "output_pending"})
        self.record._set_file_content("TEST %d" % self.record.id)
        self.assertFalse(self.record.exchanged_on)
        self.record.with_context(
            test_break_send="OOPS! Something went wrong :("
        ).action_exchange_send()
        self.assertTrue(FakeOutputSender.check_called_for(self.record))
        self.assertRecordValues(
            self.record,
            [
                {
                    "edi_exchange_state": "output_error_on_send",
                    "exchange_error": "OOPS! Something went wrong :(",
                }
            ],
        )

    def test_send_invalid_direction(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_input", vals)
        with mock.patch.object(type(self.backend), "_exchange_send") as mocked:
            mocked.return_value = "AAA"
            with self.assertRaises(UserError) as err:
                record.action_exchange_send()
            self.assertEqual(
                err.exception.name, "Record ID=%d is not meant to be sent!" % record.id
            )
            mocked.assert_not_called()

    def test_send_not_generated_record(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        with mock.patch.object(type(self.backend), "_exchange_send") as mocked:
            mocked.return_value = "AAA"
            with self.assertRaises(UserError) as err:
                record.action_exchange_send()
            self.assertEqual(
                err.exception.name, "Record ID=%d has no file to send!" % record.id
            )
            mocked.assert_not_called()
