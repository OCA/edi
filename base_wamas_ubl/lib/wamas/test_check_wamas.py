import ast
import unittest

from check_wamas import check_wamas
from utils import file_open, file_path


class TestCheckWamas(unittest.TestCase):
    knownValuesLines = (
        (
            file_open(file_path("tests/samples/check_wamas_input_lst.wamas")).read(),
            file_open(file_path("tests/samples/check_wamas_output_lst.dict")).read(),
        ),
        (
            file_open(file_path("tests/samples/check_wamas_input_aus.wamas")).read(),
            file_open(file_path("tests/samples/check_wamas_output_aus.dict")).read(),
        ),
        (
            file_open(file_path("tests/samples/check_wamas_input_art.wamas")).read(),
            file_open(file_path("tests/samples/check_wamas_output_art.dict")).read(),
        ),
    )

    def testDict2wamas(self):
        for str_input, expected_output in self.knownValuesLines:
            data, lst_telegram_type, wamas_type = check_wamas(str_input)
            dict_expected_output = ast.literal_eval(expected_output)
            # Telegram Types
            self.assertEqual(
                lst_telegram_type, dict_expected_output["lst_telegram_type"]
            )
            # Wamas Type
            self.assertEqual(wamas_type, dict_expected_output["wamas_type"])
            # Data
            self.assertEqual(data, dict_expected_output["data"])


if __name__ == "__main__":
    unittest.main()
