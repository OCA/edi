# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from freezegun import freeze_time

from odoo import exceptions, fields

from odoo.addons.queue_job.job import DelayableRecordset

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
        # create new one to delete it later
        partner = self.partner.copy({"name": "Test EDI record rel"})
        vals = {
            "model": partner._name,
            "res_id": partner.id,
        }
        record = self.backend.create_record("test_csv_output", vals)
        self.assertEqual(record.related_name, partner.name)
        record1 = self.backend.create_record(
            "test_csv_output", dict(vals, parent_id=record.id)
        )
        self.assertEqual(record1.related_name, partner.name)
        record2 = self.backend.create_record(
            "test_csv_output_ack", dict(vals, parent_id=record.id)
        )
        self.assertEqual(record2.related_name, partner.name)
        self.assertIn(record1, record.related_exchange_ids)
        self.assertIn(record2, record.related_exchange_ids)
        self.assertEqual(record.ack_exchange_id, record2)
        # Check deletion
        partner.unlink()
        self.assertFalse(record1.record)
        self.assertFalse(record1.related_name)

    def test_record_empty_with_parent(self):
        """Simulate child record doesn't have a model and res_id.

        In this case the .record should return the record of the parent.
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

    def test_with_delay_override(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_input", vals)
        parent_channel = self.env["queue.job.channel"].create(
            {
                "name": "parent_test_chan",
                "parent_id": self.env.ref("queue_job.channel_root").id,
            }
        )
        channel = self.env["queue.job.channel"].create(
            {"name": "test_chan", "parent_id": parent_channel.id}
        )
        self.exchange_type_in.job_channel_id = channel
        # re-enable job delayed feature
        delayed = record.with_context(test_queue_job_no_delay=False).with_delay()
        self.assertTrue(isinstance(delayed, DelayableRecordset))
        self.assertEqual(delayed.recordset, record)
        self.assertEqual(delayed.channel, "root.parent_test_chan.test_chan")
