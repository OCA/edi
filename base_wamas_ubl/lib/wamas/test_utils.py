import ast
import unittest

from freezegun import freeze_time
from utils import dict2wamas, file_open, file_path


class TestUtils(unittest.TestCase):
    knownValuesLines = (
        (
            "LST",
            file_open(file_path("tests/samples/dict2wamas_input.dict")).read(),
            file_open(file_path("tests/samples/dict2wamas_output.wamas"))
            .read()
            .encode("iso-8859-1"),
        ),
        (
            "KSTAUS",
            file_open(file_path("tests/samples/dict2wamas_input_2.dict")).read(),
            file_open(file_path("tests/samples/dict2wamas_output_2.wamas"))
            .read()
            .encode("iso-8859-1"),
        ),
    )

    @freeze_time("2023-12-21 04:12:51")
    def testDict2wamas(self):
        for telegram, str_dict_input, expected_output in self.knownValuesLines:
            output = dict2wamas(ast.literal_eval(str_dict_input), telegram)
            self.assertEqual(output, expected_output)


if __name__ == "__main__":
    unittest.main()
