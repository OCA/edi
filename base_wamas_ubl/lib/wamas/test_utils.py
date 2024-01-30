import ast
import unittest

import xmltodict
from dotty_dict import Dotty
from freezegun import freeze_time
from utils import (
    _set_string_bool,
    dict2wamas,
    file_open,
    file_path,
    get_address_elements,
    get_Adrs_Adr,
    get_Adrs_Name,
    get_Adrs_Name2,
    get_Adrs_Name3,
    get_Adrs_Name4,
)


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

    def testGetAddressNamePicking(self):
        infile = file_open(
            file_path("tests/samples/UBL2WAMAS-SAMPLE_AUSK_AUSP-DESPATCH_ADVICE.xml")
        ).read()
        dict_item = Dotty(xmltodict.parse(infile))
        address_elements = get_address_elements(dict_item)
        self.assertEqual(
            address_elements,
            {
                "ContactName": "Chester Reed",
                "PartyName": "YourCompany",
                "Department": "Department_1",
                "StreetName": "250 Executive Park Blvd, Suite 3400",
                "AdditionalStreetName": "AdditionalStreetName_1",
            },
        )
        self.assertEqual(get_Adrs_Name(address_elements), "Chester Reed")
        self.assertEqual(get_Adrs_Name2(address_elements), "YourCompany")
        self.assertEqual(get_Adrs_Name3(address_elements), "Department_1")
        self.assertEqual(
            get_Adrs_Name4(address_elements), "250 Executive Park Blvd, Suite 3400"
        )
        self.assertEqual(get_Adrs_Adr(address_elements), "AdditionalStreetName_1")

    def testGetAddressNameFromDict(self):
        address_elements = {
            "ContactName": "Nom",
            "PartyName": "YourCompany",
            "Department": "Nom3",
            "StreetName": "Nom4",
            "AdditionalStreetName": "Adresse",
        }
        self.assertEqual(get_Adrs_Name(address_elements), "Nom")
        self.assertEqual(get_Adrs_Name2(address_elements), "YourCompany")
        self.assertEqual(get_Adrs_Name3(address_elements), "Nom3")
        self.assertEqual(get_Adrs_Name4(address_elements), "Nom4")
        self.assertEqual(get_Adrs_Adr(address_elements), "Adresse")

    def test_set_string_bool(self):
        # Input is boolean
        self.assertEqual(_set_string_bool(False, 1, False), "N")
        self.assertEqual(_set_string_bool(True, 1, False), "J")

        # Input is string
        self.assertEqual(_set_string_bool("N", 1, False), "N")
        self.assertEqual(_set_string_bool("J", 1, False), "J")


if __name__ == "__main__":
    unittest.main()
