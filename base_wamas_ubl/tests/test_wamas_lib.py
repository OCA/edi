# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ast import literal_eval

from freezegun import freeze_time

from odoo.tests.common import TransactionCase
from odoo.tools import file_open

# FIXME: all those simple convertion tests should move to lib/wamas/tests and
# there should be a test that runs the lib tests


class TestWamasLib(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_wamas_ubl = cls.env["base.wamas.ubl"]

    @freeze_time("2023-05-01")
    def _convert_wamas2ubl(self, input_filename, expected_output_filename):
        path = "base_wamas_ubl/tests/samples/"
        with file_open(path + input_filename) as inputfile, file_open(
            path + expected_output_filename
        ) as outputfile:
            str_input = inputfile.read()
            output = "\n".join(self.base_wamas_ubl.wamas2ubl(str_input))
            expected_output = outputfile.read()
            self.assertEqual(output, expected_output)

    def test_convert_wamas2ubl_picking(self):
        input_file = "WAMAS2UBL-SAMPLE_AUSKQ_WATEKQ_WATEPQ.wamas"
        lst_expected_output = "WAMAS2UBL-SAMPLE_AUSKQ_WATEKQ_WATEPQ-DESPATCH_ADVICE.xml"
        self._convert_wamas2ubl(input_file, lst_expected_output)

    def test_convert_wamas2ubl_reception(self):
        input_file = "WAMAS2UBL-SAMPLE_WEAKQ_WEAPQ.wamas"
        lst_expected_output = "WAMAS2UBL-SAMPLE_WEAKQ_WEAPQ-DESPATCH_ADVICE.xml"
        self._convert_wamas2ubl(input_file, lst_expected_output)

    def test_convert_wamas2ubl_return(self):
        input_file = "WAMAS2UBL-SAMPLE_KRETKQ_KRETPQ.wamas"
        lst_expected_output = "WAMAS2UBL-SAMPLE_KRETKQ_KRETPQ-DESPATCH_ADVICE.xml"
        self._convert_wamas2ubl(input_file, lst_expected_output)

    @freeze_time("2023-05-01")
    def _convert_ubl2wamas(
        self, input_filename, expected_output_filename, telegram_type
    ):
        path = "base_wamas_ubl/tests/samples/"
        with file_open(path + input_filename) as inputfile, file_open(
            path + expected_output_filename
        ) as outputfile:
            str_input = inputfile.read()
            output = self.base_wamas_ubl.ubl2wamas(str_input, telegram_type)
            expected_output = outputfile.read().strip("\n")
            self.assertEqual(output, expected_output)

    def test_convert_ubl2wamas_picking(self):
        input_file = "UBL2WAMAS-SAMPLE_AUSK_AUSP-DESPATCH_ADVICE.xml"
        expected_output = "UBL2WAMAS-SAMPLE_AUSK_AUSP.wamas"
        msg_type = "Picking"
        self._convert_ubl2wamas(input_file, expected_output, msg_type)

    def test_convert_ubl2wamas_reception(self):
        input_file = "UBL2WAMAS-SAMPLE_WEAK_WEAP-DESPATCH_ADVICE.xml"
        expected_output = "UBL2WAMAS-SAMPLE_WEAK_WEAP.wamas"
        msg_type = "Reception"
        self._convert_ubl2wamas(input_file, expected_output, msg_type)

    def test_convert_ubl2wamas_return(self):
        input_file = "UBL2WAMAS-SAMPLE_KRETK_KRETP-DESPATCH_ADVICE.xml"
        expected_output = "UBL2WAMAS-SAMPLE_KRETK_KRETP.wamas"
        msg_type = "Return"
        self._convert_ubl2wamas(input_file, expected_output, msg_type)

    @freeze_time("2023-12-21 04:12:51")
    def test_export_dict2wamas(self):
        input_filename = "DICT2WAMAS-SAMPLE_INPUT.dict"
        expected_output_filename = "DICT2WAMAS-SAMPLE_OUTPUT.wamas"
        path = "base_wamas_ubl/tests/samples/"
        with file_open(path + input_filename) as inputfile, file_open(
            path + expected_output_filename
        ) as outputfile:
            dict_input = literal_eval(inputfile.read())
            output = self.base_wamas_ubl.dict2wamas(dict_input, "Supplier")
            expected_output = outputfile.read()
            self.assertEqual(output, expected_output)

    @freeze_time("2023-12-21 04:12:51")
    def test_get_wamas_type(self):
        input_filename = "CHECKWAMAS-SAMPLE_INPUT.wamas"
        expected_output_filename = "CHECKWAMAS-SAMPLE_OUTPUT.dict"
        path = "base_wamas_ubl/tests/samples/"
        with file_open(path + input_filename) as inputfile, file_open(
            path + expected_output_filename
        ) as outputfile:
            str_input = inputfile.read()
            dict_expected_output = literal_eval(outputfile.read())
            wamas_type = self.base_wamas_ubl.get_wamas_type(str_input)
            # Wamas Type
            self.assertEqual(wamas_type, dict_expected_output["wamas_type"])
