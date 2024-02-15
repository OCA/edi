# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from base64 import b64decode, b64encode

from freezegun import freeze_time

from odoo.tests.common import TransactionCase
from odoo.tools import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

# FIXME: all simple convertion tests should move to lib/wamas/tests and there
# should be a test that runs the lib tests


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
    def _wamas_ubl_wiz_check(self, input_filename, expected_output_filename):
        with file_open(input_filename) as inputfile, file_open(
            expected_output_filename
        ) as outputfile:
            str_input = inputfile.read()
            str_expected_output = outputfile.read().strip("\n")
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
        self, input_filename, expected_output_filename, state="success"
    ):
        with file_open(input_filename) as inputfile, file_open(
            expected_output_filename
        ) as outputfile:
            str_input = inputfile.read()
            expected_output = outputfile.read()
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
                self.assertEqual(output, expected_output)
            else:
                self.assertEqual(wizard.output, expected_output)

    def test_wamas_ubl_wiz_check(self):
        # Success
        self._wamas_ubl_wiz_check(
            "base_wamas_ubl/tests/samples/CHECKWAMAS-SAMPLE_INPUT.wamas",
            "base_wamas_ubl/tests/samples/CHECKWAMAS-SAMPLE_OUTPUT.txt",
        )

    def test_wamas_ubl_wiz_check_exception_1(self):
        # Raise Exception
        self._wamas_ubl_wiz_check(
            "base_wamas_ubl/tests/samples/CHECKWAMAS-SAMPLE_INPUT-EXCEPTION.wamas",
            "base_wamas_ubl/tests/samples/CHECKWAMAS-SAMPLE_OUTPUT-EXCEPTION.txt",
        )

    def test_wamas_ubl_wiz_check_exception_2(self):
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
