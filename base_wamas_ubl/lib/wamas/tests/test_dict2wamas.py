import ast
import unittest

from ..dict2wamas import dict2wamas
from ..utils import file_open, file_path


class TestDict2wamas(unittest.TestCase):
    def _test(self, msg_type, filename):
        with file_open(
            file_path("tests/samples/dict2wamas_input%s.dict" % filename)
        ) as infile, file_open(
            file_path("tests/samples/dict2wamas_output%s.wamas" % filename)
        ) as outfile:
            dict_input = ast.literal_eval(infile.read())
            output = dict2wamas(dict_input, msg_type)
            expected_output = outfile.read()
            self.assertEqual(output, expected_output)

    def test_LST(self):
        self._test("Supplier", "")

    def test_KSTAUS(self):
        self._test("CustomerDeliveryPreferences", "_2")


if __name__ == "__main__":
    unittest.main()
