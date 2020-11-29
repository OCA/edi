# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

from odoo import exceptions, fields

from .common import EDIBackendCommonTestCase


class EDIRecordTestCase(EDIBackendCommonTestCase):
    # TODO: test more

    def test_record_identifier(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        self.assertTrue(
            record.identifier.startswith("EDI/{}".format(fields.Date.today().year))
        )
        new_record = self.backend.create_record(
            "test_csv_output", dict(vals, identifier=record.identifier)
        )
        self.assertTrue(
            new_record.identifier.startswith("EDI/{}".format(fields.Date.today().year))
        )
        self.assertNotEqual(new_record.identifier, record.identifier)

    def test_record_validate_state(self):
        with self.assertRaises(exceptions.ValidationError) as err:
            vals = {
                "model": self.partner._name,
                "res_id": self.partner.id,
                "edi_exchange_state": "output_pending",
            }
            self.backend.create_record("test_csv_input", vals)
            self.assertEqual(
                err.exception.name, "Exchange state must respect direction!"
            )

    def test_record_exchange_date(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "edi_exchange_state": "output_pending",
        }
        record = self.backend.create_record("test_csv_output", vals)
        self.assertFalse(record.exchanged_on)
        with freeze_time("2020-10-21 10:00:00"):
            record.edi_exchange_state = "output_sent"
            self.assertEqual(
                fields.Datetime.to_string(record.exchanged_on), "2020-10-21 10:00:00"
            )
