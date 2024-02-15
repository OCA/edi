import unittest

from freezegun import freeze_time

from ..utils import file_open, file_path
from ..wamas2wamas import wamas2wamas


class TestWamas2wamas(unittest.TestCase):
    def _test(self, filename):
        with file_open(
            file_path("tests/samples/wamas2wamas_input_%s.wamas" % filename)
        ) as infile, file_open(
            file_path("tests/samples/wamas2wamas_output_%s.wamas" % filename)
        ) as outfile:
            str_input = infile.read()
            output = wamas2wamas(str_input)
            expected_output = outfile.read()
            self.assertEqual(output, expected_output)

    @freeze_time("2023-12-20 09:11:16")
    def testWamas2wamas(self):
        self._test("wea")


if __name__ == "__main__":
    unittest.main()
