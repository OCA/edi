# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import unittest

from freezegun import freeze_time

from ..utils import file_open, file_path
from ..wamas2ubl import wamas2ubl


class TestWamas2ubl(unittest.TestCase):

    maxDiff = None

    @freeze_time("2023-05-01")
    def _convert_wamas2ubl(self, input_filename, expected_output_filename):
        path = file_path("tests/samples/")
        with file_open(path + input_filename) as inputfile, file_open(
            path + expected_output_filename
        ) as outputfile:
            str_input = inputfile.read()
            output = "\n".join(wamas2ubl(str_input))
            expected_output = outputfile.read()
            self.assertEqual(output, expected_output)

    def test_convert_wamas2ubl_picking(self):
        input_file = "WAMAS2UBL-SAMPLE_AUSKQ_WATEKQ_WATEPQ.wamas"
        lst_expected_output = "WAMAS2UBL-SAMPLE_AUSKQ_WATEKQ_WATEPQ-DESPATCH_ADVICE.xml"
        self._convert_wamas2ubl(input_file, lst_expected_output)

    def test_convert_wamas2ubl_reception_simple(self):
        input_file = "WAMAS2UBL-SAMPLE_SIMPLE_WEAKQ_WEAPQ.wamas"
        lst_expected_output = "WAMAS2UBL-SAMPLE_SIMPLE_WEAKQ_WEAPQ-DESPATCH_ADVICE.xml"
        self._convert_wamas2ubl(input_file, lst_expected_output)

    def test_convert_wamas2ubl_reception_combined(self):
        """
        Test a reception with a single header concerning multiple receptions

        This happens when a supplier deliver goods for multiple INs
        """
        input_file = "WAMAS2UBL-SAMPLE_COMB_WEAKQ_WEAPQ.wamas"
        lst_expected_output = "WAMAS2UBL-SAMPLE_COMB_WEAKQ_WEAPQ-DESPATCH_ADVICE.xml"
        self._convert_wamas2ubl(input_file, lst_expected_output)

    def test_convert_wamas2ubl_reception_groupby(self):
        input_file = "WAMAS2UBL-SAMPLE_GROUPBY_WEAKQ_WEAPQ.wamas"
        lst_expected_output = "WAMAS2UBL-SAMPLE_GROUPBY_WEAKQ_WEAPQ-DESPATCH_ADVICE.xml"
        self._convert_wamas2ubl(input_file, lst_expected_output)

    def test_convert_wamas2ubl_return(self):
        input_file = "WAMAS2UBL-SAMPLE_KRETKQ_KRETPQ.wamas"
        lst_expected_output = "WAMAS2UBL-SAMPLE_KRETKQ_KRETPQ-DESPATCH_ADVICE.xml"
        self._convert_wamas2ubl(input_file, lst_expected_output)


if __name__ == "__main__":
    unittest.main()
