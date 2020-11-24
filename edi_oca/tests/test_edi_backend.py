# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

import mock
import psycopg2
from freezegun import freeze_time

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import EDIBackendCommonTestCase


@tagged("-at_install", "post_install")
class EDIBackendTestCase(EDIBackendCommonTestCase):
    def test_type_code(self):
        btype = self.backend_type_model.create(
            {"name": "Test new type", "code": "Test new type"}
        )
        self.assertEqual(btype.code, "test_new_type")

    def test_type_code_uniq(self):
        existing_code = self.backend.backend_type_id.code
        with mute_logger("odoo.sql_db"):
            with self.assertRaises(psycopg2.IntegrityError):
                self.backend_type_model.create(
                    {"name": "Test new type", "code": existing_code}
                )

    def test_record_state(self):
        with self.assertRaises(ValidationError):
            vals = {
                "model": self.partner._name,
                "res_id": self.partner.id,
                "edi_exchange_state": "output_pending",
            }
            self.backend.create_record("test_csv_input", vals)

    @freeze_time("2020-10-21 10:00:00")
    def test_create_record(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_input", vals)
        expected = {
            "type_id": self.exchange_type_in.id,
            "edi_exchange_state": "new",
            "exchange_filename": "EDI_EXC_TEST-test_csv_"
            "input-2020-10-21-10-00-00.csv",
        }
        self.assertRecordValues(record, [expected])
        self.assertEqual(record.record, self.partner)
        self.assertEqual(record.edi_exchange_state, "new")

    def test_generate_record_output(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        with mock.patch.object(type(self.backend), "_generate_output") as mocked:
            mocked.return_value = "Any string"
            self.backend.generate_output(record)
            mocked.assert_called_with(record)

    def test_send_record(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "edi_exchange_state": "output_pending",
            "exchange_file": base64.b64encode(b"1234"),
        }
        record = self.backend.create_record("test_csv_output", vals)
        self.assertFalse(record.exchanged_on)
        with mock.patch.object(type(self.backend), "_exchange_send") as patch:
            patch.return_value = "AAA"
            record.action_exchange_send()
            patch.assert_called()
        self.assertEqual(record.edi_exchange_state, "output_sent")
        self.assertTrue(record.exchanged_on)

    def test_send_record_with_error(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "edi_exchange_state": "output_pending",
            "exchange_file": base64.b64encode(b"1234"),
        }
        record = self.backend.create_record("test_csv_output", vals)
        record.action_exchange_send()
        self.assertEqual(record.edi_exchange_state, "output_error_on_send")

    def test_send_inbound_error(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_input", vals)
        with mock.patch.object(type(self.backend), "_exchange_send") as patch:
            patch.return_value = "AAA"
            with self.assertRaises(UserError):
                record.action_exchange_send()
            patch.assert_not_called()

    def test_send_not_generated_record(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        with mock.patch.object(type(self.backend), "_exchange_send") as patch:
            patch.return_value = "AAA"
            with self.assertRaises(UserError):
                record.action_exchange_send()
            patch.assert_not_called()

    # TODO:
    # 1. split output from incoming
    # 2. test components lookup a ComponentRegistryCase
