# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

from .common import EDIBackendCommonTestCase


class EDIBackendTestCase(EDIBackendCommonTestCase):
    def test_remote_file_path(self):
        to_test = (
            (("input", "pending", "foo.csv"), "demo_in/pending/foo.csv"),
            (("input", "done", "foo.csv"), "demo_in/done/foo.csv"),
            (("input", "error", "foo.csv"), "demo_in/error/foo.csv"),
            (("output", "pending", "foo.csv"), "demo_out/pending/foo.csv"),
            (("output", "done", "foo.csv"), "demo_out/done/foo.csv"),
            (("output", "error", "foo.csv"), "demo_out/error/foo.csv"),
        )
        for _args, expected in to_test:
            path_obj = self.backend._remote_file_path(*_args)
            self.assertEqual(path_obj.as_posix(), expected)

        with self.assertRaises(AssertionError):
            self.backend._remote_file_path("WHATEVER", "error", "foo.csv")

        with self.assertRaises(AssertionError):
            self.backend._remote_file_path("input", "WHATEVER", "foo.csv")

    @freeze_time("2020-10-21 10:00:00")
    def test_create_record(self):
        vals = {
            "model": self.partner._name,
            "res_id": self.partner.id,
        }
        record = self.backend.create_record("test_csv_input", vals)
        expected = {
            "type_id": self.exchange_type_in.id,
            "record_id": self.partner,
            "edi_exchange_state": "new",
            "exchange_filename": "EDI_EXC_TEST-test_csv_input-2020-10-21-10-00-00.csv",
        }
        self.assertRecordValues(record, [expected])
