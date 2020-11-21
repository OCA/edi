# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import psycopg2

from odoo.exceptions import ValidationError
from odoo.tools import mute_logger

from .common import EDIBackendCommonTestCase


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

    def test_create_record(self):
        with self.mocked_today("2020-10-21 10:00:00"):
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
