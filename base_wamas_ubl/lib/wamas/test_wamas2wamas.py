import unittest

from freezegun import freeze_time
from utils import file_open, file_path
from wamas2wamas import wamas2wamas


class TestWamas2wamas(unittest.TestCase):

    knownValuesLines = (
        (
            file_open(file_path("tests/samples/wamas2wamas_input_wea.wamas")).read(),
            file_open(file_path("tests/samples/wamas2wamas_output_wea.wamas")).read(),
        ),
    )

    @freeze_time("2023-12-20 09:11:16")
    def testWamas2wamas(self):
        for str_input, expected_output in self.knownValuesLines:
            output = wamas2wamas(str_input)
            self.assertEqual(output, expected_output)


if __name__ == "__main__":
    unittest.main()
