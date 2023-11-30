# Copyright 2020 ACSONE
# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

import mock
from freezegun import freeze_time

from odoo import exceptions, fields
from odoo.tools import mute_logger

from odoo.addons.edi_oca.utils import get_checksum
from odoo.addons.queue_job.delay import DelayableRecordset

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
        expected_err = "Exchange state must respect direction!"
        with self.assertRaises(exceptions.ValidationError, msg=expected_err):
            vals = {
                "model": self.partner._name,
                "res_id": self.partner.id,
                "edi_exchange_state": "output_pending",
            }
            self.backend.create_record("test_csv_input", vals)

    def test_record_same_type_code(self):
        # Two record.exchange.type sharing same code "test_csv_input"
        # Record should be created with the right backend
        new_backend = self.backend.copy()
        self.exchange_type_in.copy(
            {"backend_id": new_backend.id, "code": "test_csv_input"}
        )
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        rec1 = self.backend.create_record("test_csv_input", vals)
        rec2 = new_backend.create_record("test_csv_input", vals)
        self.assertEqual(rec1.backend_id, self.backend)
        self.assertEqual(rec2.backend_id, new_backend)

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

    @mute_logger("odoo.models.unlink")
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
        # Silent useless warning
        # `Delayable Delayable(edi.exchange.record*) was prepared but never delayed`
        delayed.delayable._generated_job = object()
        self.assertTrue(isinstance(delayed, DelayableRecordset))
        self.assertEqual(delayed.recordset, record)
        self.assertEqual(delayed.delayable.channel, "root.parent_test_chan.test_chan")

    def test_create_child(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record0 = self.backend.create_record("test_csv_output", vals)
        record1 = record0.exchange_create_child_record()
        record2 = record0.exchange_create_child_record()
        record3 = record2.exchange_create_child_record(model="sale.order", res_id=1)
        record0.invalidate_cache()
        record2.invalidate_cache()
        self.assertIn(record1, record0.related_exchange_ids)
        self.assertIn(record2, record0.related_exchange_ids)
        self.assertIn(record3, record2.related_exchange_ids)
        self.assertRecordValues(
            record1 + record2 + record3,
            [
                {
                    "parent_id": record0.id,
                    "model": "res.partner",
                    "res_id": self.partner.id,
                },
                {
                    "parent_id": record0.id,
                    "model": "res.partner",
                    "res_id": self.partner.id,
                },
                {"parent_id": record2.id, "model": "sale.order", "res_id": 1},
            ],
        )

    def test_create_ack(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record0 = self.backend.create_record("test_csv_output", vals)
        ack = record0.exchange_create_ack_record()
        record0.invalidate_cache()
        self.assertIn(ack, record0.related_exchange_ids)
        self.assertRecordValues(
            ack,
            [
                {
                    "parent_id": record0.id,
                    "model": "res.partner",
                    "res_id": self.partner.id,
                    "type_id": self.exchange_type_out_ack.id,
                },
            ],
        )
        ack2 = record0.exchange_create_ack_record()
        self.assertEqual(record0.ack_exchange_id, ack2)

    def test_retry(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record0 = self.backend.create_record("test_csv_output", vals)
        self.assertFalse(record0.retryable)
        record0.edi_exchange_state = "output_error_on_send"
        self.assertTrue(record0.retryable)
        with mock.patch.object(type(record0), "_execute_next_action") as mocked:
            record0.action_retry()
            # quick exec is off, we should not get any call
            mocked.assert_not_called()
        self.assertEqual(record0.edi_exchange_state, "output_pending")
        self.assertFalse(record0.retryable)

    def test_checksum(self):
        filecontent = base64.b64encode(b"ABC")
        checksum1 = get_checksum(filecontent)
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
            "exchange_file": filecontent,
        }
        record0 = self.backend.create_record("test_csv_output", vals)
        self.assertEqual(record0.exchange_filechecksum, checksum1)
        filecontent = base64.b64encode(b"DEF")
        checksum2 = get_checksum(filecontent)
        record0.exchange_file = filecontent
        self.assertEqual(record0.exchange_filechecksum, checksum2)
        self.assertNotEqual(record0.exchange_filechecksum, checksum1)
