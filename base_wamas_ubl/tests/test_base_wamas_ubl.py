# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ast import literal_eval
from base64 import b64decode, b64encode

from freezegun import freeze_time

from odoo.tests.common import TransactionCase
from odoo.tools import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestBaseWamas(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_wamas_ubl = cls.env["base.wamas.ubl"]
        cls.wamas_ubl_wiz_check = cls.env["wamas.ubl.wiz.check"]
        cls.wamas_ubl_wiz_simulate = cls.env["wamas.ubl.wiz.simulate"]
        cls.assertXmlTreeEqual = AccountTestInvoicingCommon.assertXmlTreeEqual
        cls.get_xml_tree_from_string = (
            AccountTestInvoicingCommon.get_xml_tree_from_string
        )
        cls._turn_node_as_dict_hierarchy = (
            AccountTestInvoicingCommon._turn_node_as_dict_hierarchy
        )
        cls.partner_1 = cls.env.ref("base.res_partner_1")
        cls.partner_2 = cls.env.ref("base.res_partner_2")
        country_code_1 = cls.partner_1.commercial_partner_id.country_id.code or ""
        country_code_2 = cls.partner_2.commercial_partner_id.country_id.code or ""
        cls.extra_data = {
            "DespatchSupplierParty": {
                "CustomerAssignedAccountID": cls.partner_1.commercial_partner_id.ref
                or "",
                "PartyName": cls.partner_1.commercial_partner_id.name or "",
                "StreetName": cls.partner_1.commercial_partner_id.street or "",
                "CityName": cls.partner_1.commercial_partner_id.city or "",
                "PostalZone": cls.partner_1.commercial_partner_id.zip or "",
                "Country.IdentificationCode": country_code_1,
                "CompanyID": cls.partner_1.commercial_partner_id.vat or "",
                "TaxScheme.ID": "",
                "TaxScheme.TaxTypeCode": "",
                "Contact.Name": cls.partner_1.child_ids
                and cls.partner_1.child_ids[0].name
                or "",
                "Contact.Telephone": cls.partner_1.child_ids
                and cls.partner_1.child_ids[0].phone
                or "",
                "Contact.ElectronicMail": cls.partner_1.child_ids
                and cls.partner_1.child_ids[0].email
                or "",
            },
            "DeliveryCustomerParty": {
                "PartyName": cls.partner_2.commercial_partner_id.name or "",
                "StreetName": cls.partner_2.commercial_partner_id.street or "",
                "CityName": cls.partner_2.commercial_partner_id.city or "",
                "PostalZone": cls.partner_2.commercial_partner_id.zip or "",
                "CountrySubentity": cls.partner_2.commercial_partner_id.state_id.name
                or "",
                "Country.IdentificationCode": country_code_2,
                "CompanyID": cls.partner_2.commercial_partner_id.vat or "",
                "TaxScheme.ID": "",
                "TaxScheme.TaxTypeCode": "",
                "Contact.Name": cls.partner_2.child_ids
                and cls.partner_2.child_ids[0].name
                or "",
                "Contact.Telephone": cls.partner_2.child_ids
                and cls.partner_2.child_ids[0].phone
                or "",
                "Contact.Telefax": "",
                "Contact.ElectronicMail": cls.partner_2.child_ids
                and cls.partner_2.child_ids[0].email
                or "",
            },
        }

    @freeze_time("2023-05-01")
    def _convert_wamas2ubl(self, input_file, expected_output_files):
        str_input = file_open(input_file, "r").read()
        outputs = self.base_wamas_ubl.wamas2ubl(str_input, self.extra_data)

        for i, output in enumerate(outputs):
            output_tree = self.get_xml_tree_from_string(output)
            expected_output = file_open(expected_output_files[i], "r").read()
            expected_output_tree = self.get_xml_tree_from_string(expected_output)
            self.assertXmlTreeEqual(output_tree, expected_output_tree)

    @freeze_time("2023-05-01")
    def _convert_ubl2wamas(self, input_file, expected_output_file, telegram_type):
        str_input = file_open(input_file, "r").read()
        output = self.base_wamas_ubl.ubl2wamas(str_input, telegram_type)
        expected_output = (
            file_open(expected_output_file, "r").read().encode("iso-8859-1")
        )
        self.assertEqual(output, expected_output)

    @freeze_time("2023-05-01")
    def _wamas_ubl_wiz_check(self, input_file, expected_output_file):
        str_input = file_open(input_file, "r").read()
        str_expected_output = file_open(expected_output_file, "r").read()
        wizard = self.wamas_ubl_wiz_check.create(
            {
                "wamas_file": b64encode(str_input.encode("iso-8859-1")),
            }
        )
        wizard._onchange_wamas_filename()
        self.assertFalse(wizard.output)
        wizard.btn_check()
        self.assertEqual(wizard.output, str_expected_output)

    @freeze_time("2023-05-01 00:00:00")
    def _wamas_ubl_wiz_simulate(
        self, input_file, expected_output_file, state="success"
    ):
        str_input = file_open(input_file, "r").read()
        wizard = self.wamas_ubl_wiz_simulate.create(
            {
                "wamas_file": b64encode(str_input.encode("iso-8859-1")),
            }
        )
        wizard._onchange_wamas_filename()
        self.assertFalse(wizard.output_wamas_file)
        self.assertFalse(wizard.output_wamas_filename)
        self.assertFalse(wizard.output)
        wizard.btn_simulate()
        if state == "success":
            output = b64decode(wizard.output_wamas_file).decode("iso-8859-1")
            expected_output = file_open(expected_output_file, "r").read()
            self.assertEqual(output, expected_output)
        else:
            expected_output = file_open(expected_output_file, "r").read()
            self.assertEqual(wizard.output, expected_output)

    def test_convert_wamas2ubl(self):
        dict_data = {
            "wamas2ubl": {
                "picking": [
                    {
                        "input_file": "base_wamas_ubl/tests/samples/"
                        "WAMAS2UBL-SAMPLE_AUSKQ_WATEKQ_WATEPQ.wamas",
                        "lst_expected_output": [
                            "base_wamas_ubl/tests/samples/"
                            "WAMAS2UBL-SAMPLE_AUSKQ_WATEKQ_WATEPQ-DESPATCH_ADVICE.xml"
                        ],
                    },
                ],
                "reception": [
                    {
                        "input_file": "base_wamas_ubl/tests/samples/"
                        "WAMAS2UBL-SAMPLE_WEAKQ_WEAPQ.wamas",
                        "lst_expected_output": [
                            "base_wamas_ubl/tests/samples/"
                            "WAMAS2UBL-SAMPLE_WEAKQ_WEAPQ-DESPATCH_ADVICE.xml"
                        ],
                    },
                    {
                        "input_file": "base_wamas_ubl/tests/samples/"
                        "WAMAS2UBL-SAMPLE_KRETKQ_KRETPQ.wamas",
                        "lst_expected_output": [
                            "base_wamas_ubl/tests/samples/"
                            "WAMAS2UBL-SAMPLE_KRETKQ_KRETPQ-DESPATCH_ADVICE.xml",
                            "base_wamas_ubl/tests/samples/"
                            "WAMAS2UBL-SAMPLE_KRETKQ_KRETPQ-DESPATCH_ADVICE-2.xml",
                        ],
                    },
                ],
            },
            "ubl2wamas": {
                "picking": [
                    {
                        "input_file": "base_wamas_ubl/tests/samples/"
                        "UBL2WAMAS-SAMPLE_AUSK_AUSP-DESPATCH_ADVICE.xml",
                        "expected_output": "base_wamas_ubl/tests/samples/"
                        "UBL2WAMAS-SAMPLE_AUSK_AUSP.wamas",
                        "type": "AUSK,AUSP",
                    },
                ],
                "reception": [
                    {
                        "input_file": "base_wamas_ubl/tests/samples/"
                        "UBL2WAMAS-SAMPLE_WEAK_WEAP-DESPATCH_ADVICE.xml",
                        "expected_output": "base_wamas_ubl/tests/samples/"
                        "UBL2WAMAS-SAMPLE_WEAK_WEAP.wamas",
                        "type": "WEAK,WEAP",
                    },
                    {
                        "input_file": "base_wamas_ubl/tests/samples/"
                        "UBL2WAMAS-SAMPLE_KRETK_KRETP-DESPATCH_ADVICE.xml",
                        "expected_output": "base_wamas_ubl/tests/samples/"
                        "UBL2WAMAS-SAMPLE_KRETK_KRETP.wamas",
                        "type": "KRETK,KRETP",
                    },
                ],
            },
        }

        # ==== wamas2ubl ====
        # picking
        for data in dict_data["wamas2ubl"]["picking"]:
            self._convert_wamas2ubl(data["input_file"], data["lst_expected_output"])

        # reception
        for data in dict_data["wamas2ubl"]["reception"]:
            self._convert_wamas2ubl(data["input_file"], data["lst_expected_output"])

        # ==== ubl2wamas ====
        # picking
        for data in dict_data["ubl2wamas"]["picking"]:
            self._convert_ubl2wamas(
                data["input_file"], data["expected_output"], data["type"]
            )

        # reception
        for data in dict_data["ubl2wamas"]["reception"]:
            self._convert_ubl2wamas(
                data["input_file"], data["expected_output"], data["type"]
            )

    @freeze_time("2023-12-21 04:12:51")
    def test_export_dict2wamas(self):
        dict_data = {
            "input": "base_wamas_ubl/tests/samples/DICT2WAMAS-SAMPLE_INPUT.dict",
            "expected_output": "base_wamas_ubl/tests/samples/DICT2WAMAS-SAMPLE_OUTPUT.wamas",
        }
        expected_output = (
            file_open(dict_data["expected_output"], "r").read().encode("iso-8859-1")
        )
        dict_input = literal_eval(file_open(dict_data["input"], "r").read())
        output = self.base_wamas_ubl.dict2wamas(dict_input, "LST")
        self.assertEqual(output, expected_output)

    @freeze_time("2023-12-21 04:12:51")
    def test_get_wamas_type(self):
        dict_data = {
            "input": "base_wamas_ubl/tests/samples/CHECKWAMAS-SAMPLE_INPUT.wamas",
            "expected_output": "base_wamas_ubl/tests/samples/CHECKWAMAS-SAMPLE_OUTPUT.dict",
        }
        str_input = file_open(dict_data["input"], "r").read()
        dict_expected_output = literal_eval(
            file_open(dict_data["expected_output"], "r").read()
        )
        dummy, lst_telegram_type, wamas_type = self.base_wamas_ubl.get_wamas_type(
            str_input
        )
        # Telegram Types
        self.assertEqual(lst_telegram_type, dict_expected_output["lst_telegram_type"])
        # Wamas Type
        self.assertEqual(wamas_type, dict_expected_output["wamas_type"])

    def test_wamas_ubl_wiz_check(self):
        # Success
        self._wamas_ubl_wiz_check(
            "base_wamas_ubl/tests/samples/CHECKWAMAS-SAMPLE_INPUT.wamas",
            "base_wamas_ubl/tests/samples/CHECKWAMAS-SAMPLE_OUTPUT.txt",
        )
        # Raise Exception
        self._wamas_ubl_wiz_check(
            "base_wamas_ubl/tests/samples/CHECKWAMAS-SAMPLE_INPUT-EXCEPTION.wamas",
            "base_wamas_ubl/tests/samples/CHECKWAMAS-SAMPLE_OUTPUT-EXCEPTION.txt",
        )
        self._wamas_ubl_wiz_check(
            "base_wamas_ubl/tests/samples/CHECKWAMAS-SAMPLE_INPUT-EXCEPTION-2.wamas",
            "base_wamas_ubl/tests/samples/CHECKWAMAS-SAMPLE_OUTPUT-EXCEPTION-2.txt",
        )

    def test_wamas_ubl_wiz_simulate(self):
        # Success
        self._wamas_ubl_wiz_simulate(
            "base_wamas_ubl/tests/samples/SIMULATEWAMAS-SAMPLE_INPUT.wamas",
            "base_wamas_ubl/tests/samples/SIMULATEWAMAS-SAMPLE_OUTPUT.wamas",
        )
        # Raise Exception
        self._wamas_ubl_wiz_simulate(
            "base_wamas_ubl/tests/samples/SIMULATEWAMAS-SAMPLE_INPUT-EXCEPTION.wamas",
            "base_wamas_ubl/tests/samples/SIMULATEWAMAS-SAMPLE_OUTPUT-EXCEPTION.txt",
            "fail",
        )
