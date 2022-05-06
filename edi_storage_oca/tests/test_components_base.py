# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import mock

from .common import STORAGE_BACKEND_MOCK_PATH, TestEDIStorageBase


class EDIStorageComponentTestCase(TestEDIStorageBase):
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
            direction, state, filename = _args
            if direction == "input":
                checker = self.checker_input
            else:
                checker = self.checker
            path_obj = checker._get_remote_file_path(state, filename)
            self.assertEqual(path_obj.as_posix(), expected)

        with self.assertRaises(AssertionError):
            self.checker_input._get_remote_file_path("WHATEVER", "foo.csv")

    def test_get_remote_file(self):
        with mock.patch(STORAGE_BACKEND_MOCK_PATH + ".get") as mocked:
            self.checker._get_remote_file("pending")
            mocked.assert_called_with(
                "demo_out/pending/{}".format(self._filename(self.record)), binary=False
            )
            self.checker._get_remote_file("done")
            mocked.assert_called_with(
                "demo_out/done/{}".format(self._filename(self.record)), binary=False
            )
            self.checker._get_remote_file("error")
            mocked.assert_called_with(
                "demo_out/error/{}".format(self._filename(self.record)), binary=False
            )
