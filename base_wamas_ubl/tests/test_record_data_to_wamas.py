# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ast import literal_eval

from freezegun import freeze_time

from odoo.tests import common
from odoo.tools import file_open


class TestRecordToWAMAS(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_wamas_ubl = cls.env["base.wamas.ubl"]

    def test_export_without_telegram(self):
        with self.assertRaisesRegex(
            ValueError, r"Please define wamas message type \(msg_type\)."
        ):
            input_dict = {"name": "David", "age": 16}
            self.env["base.wamas.ubl"].record_data_to_wamas(input_dict, "")

    def test_export_invalid_dict(self):
        with self.assertRaisesRegex(ValueError, "The data is not valid."):
            input_dict = ["David", 16]
            self.base_wamas_ubl.record_data_to_wamas(input_dict, "Supplier")

    @freeze_time("2023-12-21 04:12:51")
    def test_export_with_LST_telegram(self):
        dict_data = {
            "input": "base_wamas_ubl/tests/samples/TELEGRAM-SAMPLE-LST_INPUT.dict",
            "expected_output": "base_wamas_ubl/tests/samples/TELEGRAM-SAMPLE-LST_OUTPUT.wamas",
        }
        expected_output = file_open(dict_data["expected_output"], "r").read()
        dict_input = literal_eval(file_open(dict_data["input"], "r").read())
        output = self.base_wamas_ubl.record_data_to_wamas(dict_input, "Supplier")
        self.assertEqual(output, expected_output)

    @freeze_time("2023-12-21 04:12:51")
    def test_export_with_KST_telegram(self):
        dict_data = {
            "input": "base_wamas_ubl/tests/samples/TELEGRAM-SAMPLE-KST_INPUT.dict",
            "expected_output": "base_wamas_ubl/tests/samples/TELEGRAM-SAMPLE-KST_OUTPUT.wamas",
        }
        expected_output = file_open(dict_data["expected_output"], "r").read()
        dict_input = literal_eval(file_open(dict_data["input"], "r").read())
        output = self.base_wamas_ubl.record_data_to_wamas(dict_input, "Customer")
        self.assertEqual(output, expected_output)

    @freeze_time("2023-12-21 04:12:51")
    def test_export_with_ART_telegram(self):
        dict_data = {
            "input": "base_wamas_ubl/tests/samples/TELEGRAM-SAMPLE-ART_INPUT.dict",
            "expected_output": "base_wamas_ubl/tests/samples/TELEGRAM-SAMPLE-ART_OUTPUT.wamas",
        }
        expected_output = (
            file_open(dict_data["expected_output"], "r").read().strip("\n")
        )
        dict_input = literal_eval(file_open(dict_data["input"], "r").read())
        output = self.base_wamas_ubl.record_data_to_wamas(dict_input, "Product")
        self.assertEqual(output, expected_output)

    @freeze_time("2023-12-21 04:12:51")
    def test_export_with_ARTE_telegram(self):
        dict_data = {
            "input": "base_wamas_ubl/tests/samples/TELEGRAM-SAMPLE-ARTE_INPUT.dict",
            "expected_output": "base_wamas_ubl/tests/samples/TELEGRAM-SAMPLE-ARTE_OUTPUT.wamas",
        }
        expected_output = file_open(dict_data["expected_output"], "r").read()
        dict_input = literal_eval(file_open(dict_data["input"], "r").read())
        output = self.base_wamas_ubl.record_data_to_wamas(dict_input, "Packaging")
        self.assertEqual(output, expected_output)

    @freeze_time("2023-12-21 04:12:51")
    def test_export_with_ARTEAN_telegram(self):
        dict_data = {
            "input": "base_wamas_ubl/tests/samples/TELEGRAM-SAMPLE-ARTEAN_INPUT.dict",
            "expected_output": "base_wamas_ubl/tests/samples/TELEGRAM-SAMPLE-ARTEAN_OUTPUT"
            ".wamas",
        }
        expected_output = file_open(dict_data["expected_output"], "r").read()
        dict_input = literal_eval(file_open(dict_data["input"], "r").read())
        output = self.base_wamas_ubl.record_data_to_wamas(dict_input, "Barcode")
        self.assertEqual(output, expected_output)

    @freeze_time("2023-12-21 04:12:51")
    def test_export_with_KSTAUS_telegram(self):
        dict_data = {
            "input": "base_wamas_ubl/tests/samples/TELEGRAM-SAMPLE-KSTAUS_INPUT.dict",
            "expected_output": "base_wamas_ubl/tests/samples/TELEGRAM-SAMPLE-KSTAUS_OUTPUT"
            ".wamas",
        }
        expected_output = file_open(dict_data["expected_output"], "r").read()
        dict_input = literal_eval(file_open(dict_data["input"], "r").read())
        output = self.base_wamas_ubl.record_data_to_wamas(
            dict_input, "CustomerDeliveryPreferences"
        )
        self.assertEqual(output, expected_output)
