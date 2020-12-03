# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

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
            [
                "edi.input.process.demo_backend.test_csv_input",
                "edi.input.process.demo_backend",
            ],
        )
        record = self.backend.create_record("test_csv_output", vals)
        candidates = self.backend._get_component_usage_candidates(record, "generate")
        self.assertEqual(
            candidates,
            [
                "edi.output.generate.demo_backend.test_csv_output",
                "edi.output.generate.demo_backend",
            ],
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
            [
                "my.special.generate",
                "edi.output.generate.demo_backend.test_csv_output",
                "edi.output.generate.demo_backend",
            ],
        )
        candidates = self.backend._get_component_usage_candidates(record, "send")
        self.assertEqual(
            candidates,
            [
                "my.special.send",
                "edi.output.send.demo_backend.test_csv_output",
                "edi.output.send.demo_backend",
            ],
        )
