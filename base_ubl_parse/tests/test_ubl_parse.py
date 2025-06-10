# Copyright 2025 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from lxml import etree

from odoo.tests.common import TransactionCase
from odoo.tools.misc import file_open, file_path


class TestBaseUblParse(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_ubl = cls.env["base.ubl"]
        cls.inv_filepath = file_path(
            "base_ubl_parse/tests/samples/UBL-Invoice-2.1-Example.xml"
        )
        cls.ord_filepath = file_path(
            "base_ubl_parse/tests/samples/UBL-Order-2.1-Example.xml"
        )
        cls.ns = {
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",  # noqa
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",  # noqa
        }

    def _get_xml_root(self, file_path):
        with file_open(file_path) as f:
            return etree.parse(f).getroot()

    def test_ubl_get_version(self):
        xml = etree.fromstring(
            b'<Invoice xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">'  # noqa
            b"<cbc:UBLVersionID>2.1</cbc:UBLVersionID></Invoice>"
        )
        version = self.base_ubl._ubl_get_version(
            xml,
            "Invoice",
            {
                "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"  # noqa
            },
        )
        self.assertEqual(version, "2.1")

    def test_ubl_parse_customer_party(self):
        root = self._get_xml_root(self.inv_filepath)
        party_node = root.find(".//cac:AccountingCustomerParty", namespaces=self.ns)
        parsed = parsed = self.base_ubl.ubl_parse_customer_party(party_node, self.ns)
        expected = {
            "vat": "BE54321",
            "name": "Buyercompany ltd",
            "website": False,
            "contact": False,
            "email": "john@buyercompany.eu",
            "phone": "5121230",
            "id_number": [{"value": "345KS5324", "schemeID": "ZZZ"}],
            "street": "Anystreet",
            "street_number": "8",
            "street2": "Back door",
            "city": "Anytown",
            "zip": "101",
            "state_code": False,
            "country_code": "BE",
            "ref": False,
        }
        self.assertEqual(parsed, expected)

    def test_ubl_parse_supplier_party(self):
        root = self._get_xml_root(self.inv_filepath)
        party_node = root.find(".//cac:AccountingSupplierParty", namespaces=self.ns)
        parsed = self.base_ubl.ubl_parse_supplier_party(party_node, self.ns)
        expected = {
            "city": "Big city",
            "contact": False,
            "country_code": "DK",
            "email": "antonio@salescompany.dk",
            "id_number": [{"schemeID": "ZZZ", "value": "Supp123"}],
            "name": "Salescompany ltd.",
            "phone": "4621230",
            "ref": False,
            "state_code": "RegionA",
            "street": "Main street",
            "street2": "Suite 123",
            "street_number": "1",
            "vat": "DK12345",
            "website": False,
            "zip": "54321",
        }
        self.assertEqual(parsed, expected)

    def test_ubl_parse_party(self):
        root = self._get_xml_root(self.inv_filepath)
        party_node = root.find(".//cac:Party", namespaces=self.ns)
        parsed = self.base_ubl.ubl_parse_party(party_node, self.ns)
        expected = {
            "city": "Big city",
            "contact": False,
            "country_code": "DK",
            "email": "antonio@salescompany.dk",
            "id_number": [{"schemeID": "ZZZ", "value": "Supp123"}],
            "name": "Salescompany ltd.",
            "phone": "4621230",
            "state_code": "RegionA",
            "street": "Main street",
            "street2": "Suite 123",
            "street_number": "1",
            "vat": "DK12345",
            "website": False,
            "zip": "54321",
        }
        self.assertEqual(parsed, expected)

    def test_ubl_parse_address(self):
        root = self._get_xml_root(self.inv_filepath)
        address_node = root.find(".//cac:PostalAddress", namespaces=self.ns)
        parsed = self.base_ubl.ubl_parse_address(address_node, self.ns)
        expected = {
            "street": "Main street",
            "street_number": "1",
            "street2": "Suite 123",
            "city": "Big city",
            "zip": "54321",
            "state_code": "RegionA",
            "country_code": "DK",
        }
        self.assertEqual(parsed, expected)

    def test_ubl_parse_delivery(self):
        root = self._get_xml_root(self.ord_filepath)
        delivery_node = root.find(".//cac:Delivery", namespaces=self.ns)
        parsed = self.base_ubl.ubl_parse_delivery(delivery_node, self.ns)
        expected = {
            "city": "Stockholm",
            "contact": "Per",
            "country_code": "SE",
            "email": "bill@svetruck.se",
            "id_number": [{"schemeID": "GLN", "value": "67654328394567"}],
            "name": "Swedish trucking",
            "phone": "987098709",
            "state_code": False,
            "street": "Rådhusgatan",
            "street2": "2nd floor",
            "street_number": "5",
            "vat": False,
            "website": False,
            "zip": "11000",
        }
        self.assertEqual(parsed, expected)

    def test_ubl_parse_delivery_details(self):
        root = self._get_xml_root(self.ord_filepath)
        delivery_node = root.find(".//cac:Delivery", namespaces=self.ns)
        parsed = self.base_ubl.ubl_parse_delivery_details(delivery_node, self.ns)
        expected = {"commitment_date": "2010-02-10 11:30"}
        self.assertEqual(parsed, expected)

    def test_ubl_parse_incoterm(self):
        root = self._get_xml_root(self.ord_filepath)
        delivery_term_node = root.find(".//cac:DeliveryTerms", namespaces=self.ns)
        parsed = self.base_ubl.ubl_parse_incoterm(delivery_term_node, self.ns)
        expected = {"code": "FOT"}
        self.assertEqual(parsed, expected)

    def test_ubl_parse_product(self):
        root = self._get_xml_root(self.inv_filepath)
        line_node = root.find(".//cac:InvoiceLine", namespaces=self.ns)
        parsed = self.base_ubl.ubl_parse_product(line_node, self.ns)
        expected = {"barcode": "1234567890124", "code": "JB007"}
        self.assertEqual(parsed, expected)
