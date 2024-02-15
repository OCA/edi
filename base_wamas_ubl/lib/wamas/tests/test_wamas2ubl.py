# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import unittest
from pprint import pformat

from ..utils import file_open, file_path
from ..wamas2ubl import wamas2dict


class TestWamas2dict(unittest.TestCase):
    def _test(self, filename):
        with file_open(
            file_path("tests/samples/%s.wamas" % filename)
        ) as infile, file_open(
            file_path("tests/samples/%s.dict" % filename)
        ) as outfile:
            str_input = infile.read()
            expected_output = outfile.read()
            output_prettified = pformat(wamas2dict(str_input))
            self.assertEqual(output_prettified, expected_output)

    def test_normal(self):
        self._test("line_WATEPQ_-_normal")

    def test_non_ascii(self):
        self._test("line_WATEPQ_-_non_ascii")

    def test_length_off(self):
        self._test("line_WATEKQ_-_length_off_by_one_01")


if __name__ == "__main__":
    unittest.main()
