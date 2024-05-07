import unittest

import xmltodict
from dotty_dict import Dotty

from ..utils import (
    _set_string_bool,
    _set_string_float,
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
    def testGetAddressNamePicking(self):
        with file_open(
            file_path("tests/samples/UBL2WAMAS-SAMPLE_AUSK_AUSP-DESPATCH_ADVICE.xml")
        ) as infile:
            dict_item = Dotty(xmltodict.parse(infile.read()))
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

    def test_set_string_float(self):
        # Positive
        self.assertEqual(_set_string_float(3.6, 9, 3), "000003600")
        self.assertEqual(_set_string_float(3.0, 9, 3), "000003000")

        # Negative
        self.assertEqual(_set_string_float(-3.6, 9, 3), "-00003600")
        self.assertEqual(_set_string_float(-3.0, 9, 3), "-00003000")


if __name__ == "__main__":
    unittest.main()
