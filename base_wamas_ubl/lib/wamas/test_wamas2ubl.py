import io
import unittest
from pprint import pprint

from utils import file_open, file_path
from wamas2ubl import wamas2dict


class TestWamas2ubl(unittest.TestCase):

    knownValuesLines = (
        (
            file_open(file_path("tests/samples/line_WATEPQ_-_normal.wamas")).read(),
            file_open(file_path("tests/samples/line_WATEPQ_-_normal.dict")).read(),
        ),
        (
            file_open(
                file_path("tests/samples/line_WATEPQ_-_weirdly_encoded_01.wamas")
            ).read(),
            file_open(
                file_path("tests/samples/line_WATEPQ_-_weirdly_encoded_01.dict")
            ).read(),
        ),
        (
            file_open(
                file_path("tests/samples/line_WATEKQ_-_length_off_by_one_01.wamas")
            ).read(),
            file_open(
                file_path("tests/samples/line_WATEKQ_-_length_off_by_one_01.dict")
            ).read(),
        ),
    )

    def testWamas2dict(self):
        for str_input, expected_output in self.knownValuesLines:
            # pprint(wamas2dict(str_input), open('tmp.dict', 'w'))
            output_prettified = io.StringIO()
            pprint(wamas2dict(str_input)[0], output_prettified)
            output_prettified = output_prettified.getvalue()
            self.assertEqual(output_prettified, expected_output)


if __name__ == "__main__":
    unittest.main()
