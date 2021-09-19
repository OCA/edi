# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from freezegun import freeze_time

from odoo.addons.queue_job.job import DelayableRecordset

from .common import EDIBackendCommonTestCase


class EDIBackendTestCase(EDIBackendCommonTestCase):
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

    def test_get_component_usage(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_input", vals)
        candidates = self.backend._get_component_usage_candidates(record, "process")
        self.assertEqual(
            candidates,
            ["input.process"],
        )
        record = self.backend.create_record("test_csv_output", vals)
        candidates = self.backend._get_component_usage_candidates(record, "generate")
        self.assertEqual(
            candidates,
            ["output.generate"],
        )
        # set advanced settings on type
        settings = """
        components:
            generate:
                usage: my.special.generate
            send:
                usage: my.special.send
        """
        record.type_id.advanced_settings_edit = settings
        candidates = self.backend._get_component_usage_candidates(record, "generate")
        self.assertEqual(
            candidates,
            ["my.special.generate", "output.generate"],
        )
        candidates = self.backend._get_component_usage_candidates(record, "send")
        self.assertEqual(
            candidates,
            ["my.special.send", "output.send"],
        )

    def test_delay_action_init(self):
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
        backend = self.backend.with_context(test_queue_job_no_delay=None)
        delayed = backend._delay_action(record)
        self.assertTrue(isinstance(delayed, DelayableRecordset))
        self.assertEqual(delayed.recordset, self.backend)
        self.assertEqual(delayed.channel, "root.parent_test_chan.test_chan")
