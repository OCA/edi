import unittest
from datetime import date, datetime

from ..utils import set_value_to_string


class TestUbl2wamas(unittest.TestCase):
    def test_helpers(self):
        dict_data = {
            "str": [
                {
                    "input_val": "WEAPQ0050",
                    "expected_output_val": "WEAPQ0050",
                    "length": 9,
                    "dp": False,
                },
            ],
            "int": [
                {
                    "input_val": 30,
                    "expected_output_val": "000030",
                    "length": 6,
                    "dp": False,
                },
                {
                    "input_val": "30",
                    "expected_output_val": "000030",
                    "length": 6,
                    "dp": False,
                },
            ],
            "float": [
                {
                    "input_val": 5184.0,
                    "expected_output_val": "000005184000",
                    "length": 12,
                    "dp": 3,
                },
                {
                    "input_val": "5184.0",
                    "expected_output_val": "000005184000",
                    "length": 12,
                    "dp": 3,
                },
            ],
            "date": [
                {
                    "input_val": "2023-05-01",
                    "expected_output_val": "20230501",
                    "length": 8,
                    "dp": False,
                },
                {
                    "input_val": date(2023, 5, 1),
                    "expected_output_val": "20230501",
                    "length": 8,
                    "dp": False,
                },
                {
                    "input_val": datetime(2023, 5, 1, 0, 0),
                    "expected_output_val": "20230501",
                    "length": 8,
                    "dp": False,
                },
            ],
            "datetime": [
                {
                    "input_val": "2023-05-01 06:57:23",
                    "expected_output_val": "20230501085723",
                    "length": 14,
                    "dp": False,
                },
                {
                    "input_val": datetime(2023, 5, 1, 6, 57, 23),
                    "expected_output_val": "20230501",
                    "length": 8,
                    "dp": False,
                },
            ],
            "bool": [
                {
                    "input_val": "N",
                    "expected_output_val": "N",
                    "length": 1,
                    "dp": False,
                },
            ],
        }

        for ttype in dict_data:
            for data in dict_data[ttype]:
                input_val = data["input_val"]
                expected_output_val = data["expected_output_val"]
                length = data["length"]
                dp = data["dp"]

                output_val = set_value_to_string(
                    input_val, ttype, length, dp, do_convert_tz=True
                )
                self.assertEqual(output_val, expected_output_val)


if __name__ == "__main__":
    unittest.main()
