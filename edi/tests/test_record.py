# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

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

    def test_record_relation(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        record1 = self.backend.create_record(
            "test_csv_output", dict(vals, parent_id=record.id)
        )
        record2 = self.backend.create_record(
            "test_csv_output_ack", dict(vals, parent_id=record.id)
        )
        self.assertIn(record1, record.related_exchange_ids)
        self.assertIn(record2, record.related_exchange_ids)
        self.assertEqual(record.ack_exchange_id, record2)

    def test_record_empty_with_parent(self):
        """
        Simulate the case when the child record doesn't have a model and res_id.
        In this case the .record should return the record of the parent.
        :return:
        """
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        record1 = self.backend.create_record(
            "test_csv_output", dict(vals, parent_id=record.id)
        )
        self.assertTrue(record1.model)
        self.assertEqual(record.record, record1.record)
        # Don't use the vals to lets empty model and res_id
        record2 = self.backend.create_record(
            "test_csv_output_ack", dict(parent_id=record.id)
        )
        self.assertFalse(record2.model)
        self.assertEqual(record.record, record2.record)
