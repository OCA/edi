# Copyright 2025 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from io import BytesIO
from unittest import mock

from lxml import etree

from odoo.tests.common import TransactionCase

from .common import DummyRecord


class TestBaseUblGenerate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_ubl = cls.env["base.ubl"]
        cls.nsmap, cls.ns = cls.base_ubl._ubl_get_nsmap_namespace("Invoice")
        cls.partner = DummyRecord(
            name="Test Partner",
            street="Street 1",
            street2="Street 2",
            street3="Street 3",
            city="Testville",
            zip="12345",
            state_id=DummyRecord(name="Test State", code="TS"),
            country_id=DummyRecord(code="IT", name="Italy"),
            parent_id=None,
            phone="123456789",
            email="test@example.com",
            lang="en_US",
            commercial_partner_id=None,
            vat="IT123456789",
            website="https://test.com",
            is_company=True,
        )
        cls.partner.commercial_partner_id = cls.partner
        cls.company = DummyRecord(partner_id=cls.partner)
        cls.uom = DummyRecord(name="Unit", unece_code="EA")
        cls.currency = DummyRecord(name="EUR")
        cls.product = DummyRecord(
            name="Test Product",
            default_code="TP001",
            attribute_line_ids=DummyRecord(
                value_ids=DummyRecord(
                    _iter=[
                        DummyRecord(name="Red", attribute_id=DummyRecord(name="Color")),
                        DummyRecord(
                            name="Large", attribute_id=DummyRecord(name="Color")
                        ),
                    ]
                ),
                attribute_id=DummyRecord(name="Color"),
            ),
            barcode="1234567890123",
            taxes_id=[],
            supplier_taxes_id=[],
        )
        cls.tax = DummyRecord(
            name="VAT 22%",
            unece_categ_id=True,
            unece_categ_code="S",
            amount_type="percent",
            amount=22.0,
            unece_type_id=True,
            unece_type_code="VAT",
        )
        cls.payment_term = DummyRecord(name="30 days")
        cls.incoterm = DummyRecord(code="EXW")
        cls.buffer = BytesIO(b"PDFDATA")
        cls.pdf_content = b"PDFDATA"
        cls.xml_string = "<xml>UBL</xml>"
        cls.xml_filename = "ubl.xml"

    def test_ubl_add_country(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_country(self.partner.country_id, root, self.ns)
        country = root.find(self.ns["cac"] + "Country")
        self.assertIsNotNone(country)
        self.assertEqual(country.find(self.ns["cbc"] + "IdentificationCode").text, "IT")
        self.assertEqual(country.find(self.ns["cbc"] + "Name").text, "Italy")

    def test_ubl_add_address(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_address(self.partner, "PostalAddress", root, self.ns)
        address = root.find(self.ns["cac"] + "PostalAddress")
        self.assertEqual(address.find(self.ns["cbc"] + "Department").text, "Street 1")
        self.assertEqual(address.find(self.ns["cbc"] + "StreetName").text, "Street 2")
        self.assertEqual(
            address.find(self.ns["cbc"] + "AdditionalStreetName").text, "Street 3"
        )
        self.assertEqual(address.find(self.ns["cbc"] + "CityName").text, "Testville")

    def test_ubl_get_contact_id(self):
        self.assertFalse(self.base_ubl._ubl_get_contact_id(self.partner))

    def test_ubl_add_contact(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_contact(self.partner, root, self.ns)
        contact = root.find(self.ns["cac"] + "Contact")
        self.assertIsNotNone(contact)
        self.assertEqual(contact.find(self.ns["cbc"] + "Telephone").text, "123456789")
        self.assertEqual(
            contact.find(self.ns["cbc"] + "ElectronicMail").text, "test@example.com"
        )

    def test_ubl_add_language(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_language("en_US", root, self.ns)
        language = root.find(self.ns["cac"] + "Language")
        self.assertEqual(language.find(self.ns["cbc"] + "LocaleCode").text, "en_US")
        self.assertEqual(language.find(self.ns["cbc"] + "Name").text, "English (US)")

    def test_ubl_get_party_identification(self):
        self.assertEqual(self.base_ubl._ubl_get_party_identification(self.partner), {})

    def test_ubl_add_party_identification(self):
        root = etree.Element(self.ns["cac"] + "Root")
        id_info = {
            "id": "IT123456789",
            "name": "VAT",
            "agency_id": "UNECE",
            "agency_name": "United Nations Economic Commission for Europe",
        }
        with mock.patch.object(
            type(self.base_ubl),
            "_ubl_get_party_identification",
            return_value=id_info,
        ):
            self.base_ubl._ubl_add_party_identification(self.partner, root, self.ns)
            party_id = root.find(self.ns["cac"] + "PartyIdentification")
            txts = [el.text for el in party_id.findall(self.ns["cbc"] + "ID")]
            self.assertEqual(
                txts,
                [
                    "IT123456789",
                    "VAT",
                    "UNECE",
                    "United Nations Economic Commission for Europe",
                ],
            )

    def test_ubl_get_tax_scheme_dict_from_partner(self):
        d = self.base_ubl._ubl_get_tax_scheme_dict_from_partner(self.partner)
        self.assertEqual(d, {"id": "VAT", "name": False, "type_code": False})

    def test_ubl_add_party_tax_scheme(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_party_tax_scheme(self.partner, root, self.ns)
        party_tax_scheme = root.find(self.ns["cac"] + "PartyTaxScheme")
        self.assertIsNotNone(party_tax_scheme)
        self.assertEqual(
            party_tax_scheme.find(self.ns["cbc"] + "CompanyID").text, "IT123456789"
        )

    def test_ubl_add_party_legal_entity(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_party_legal_entity(self.partner, root, self.ns)
        ple = root.find(self.ns["cac"] + "PartyLegalEntity")
        self.assertIsNotNone(ple)
        self.assertEqual(
            ple.find(self.ns["cbc"] + "RegistrationName").text, "Test Partner"
        )

    def test_ubl_add_party(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_party(self.partner, self.company, "Party", root, self.ns)
        party = root.find(self.ns["cac"] + "Party")
        self.assertIsNotNone(party)
        self.assertEqual(
            party.find(self.ns["cac"] + "PartyName").find(self.ns["cbc"] + "Name").text,
            "Test Partner",
        )

    def test_ubl_get_customer_assigned_id(self):
        self.assertEqual(
            self.base_ubl._ubl_get_customer_assigned_id(self.partner), None
        )

    def test_ubl_add_customer_party(self):
        root = etree.Element(self.ns["cac"] + "Root")
        node = self.base_ubl._ubl_add_customer_party(
            self.partner, self.company, "CustomerParty", root, self.ns
        )
        self.assertIsNotNone(node)
        self.assertEqual(node.tag, self.ns["cac"] + "CustomerParty")

    def test_ubl_add_supplier_party(self):
        root = etree.Element(self.ns["cac"] + "Root")
        node = self.base_ubl._ubl_add_supplier_party(
            self.partner, self.company, "SupplierParty", root, self.ns
        )
        self.assertIsNotNone(node)
        self.assertEqual(node.tag, self.ns["cac"] + "SupplierParty")

    def test_ubl_add_delivery(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_delivery(self.partner, root, self.ns)
        delivery = root.find(self.ns["cac"] + "Delivery")
        self.assertIsNotNone(delivery)

    def test_ubl_add_delivery_terms(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_delivery_terms(self.incoterm, root, self.ns)
        delivery_term = root.find(self.ns["cac"] + "DeliveryTerms")
        self.assertIsNotNone(delivery_term)
        self.assertEqual(delivery_term.find(self.ns["cbc"] + "ID").text, "EXW")

    def test_ubl_add_payment_terms(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_payment_terms(self.payment_term, root, self.ns)
        pay_term = root.find(self.ns["cac"] + "PaymentTerms")
        self.assertIsNotNone(pay_term)
        self.assertEqual(pay_term.find(self.ns["cbc"] + "Note").text, "30 days")

    def test_ubl_add_line_item(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_line_item(
            1,
            "Test Item",
            self.product,
            "purchase",
            2,
            self.uom,
            root,
            self.ns,
            currency=self.currency,
            price_subtotal=20.0,
        )
        line_item = root.find(self.ns["cac"] + "LineItem")
        self.assertIsNotNone(line_item)
        self.assertEqual(line_item.find(self.ns["cbc"] + "ID").text, "1")

    def test_ubl_get_seller_code_from_product(self):
        self.assertEqual(
            self.base_ubl._ubl_get_seller_code_from_product(self.product), "TP001"
        )

    def test_ubl_get_customer_product_code(self):
        self.assertEqual(
            self.base_ubl._ubl_get_customer_product_code(self.product, self.partner), ""
        )

    def test_ubl_add_item(self):
        root = etree.Element(self.ns["cac"] + "Root")
        node = self.base_ubl._ubl_add_item("Test Item", self.product, root, self.ns)
        self.assertIsNotNone(node)
        self.assertEqual(node.tag, self.ns["cac"] + "Item")

    def test_ubl_add_tax_subtotal(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_tax_subtotal(100, 22, self.tax, "EUR", root, self.ns)
        tax_subtotal = root.find(self.ns["cac"] + "TaxSubtotal")
        taxable_amount = tax_subtotal.find(self.ns["cbc"] + "TaxableAmount")
        self.assertEqual(taxable_amount.text, "100.00")

    def test_ubl_add_tax_category(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_tax_category(self.tax, root, self.ns)
        tax_category = root.find(self.ns["cac"] + "TaxCategory")
        self.assertIsNotNone(tax_category)
        self.assertEqual(tax_category.find(self.ns["cbc"] + "ID").text, "S")

    def test_ubl_get_tax_scheme_dict_from_tax(self):
        d = self.base_ubl._ubl_get_tax_scheme_dict_from_tax(self.tax)
        self.assertEqual(d, {"id": "VAT", "name": False, "type_code": False})

    def test_ubl_add_tax_scheme(self):
        root = etree.Element(self.ns["cac"] + "Root")
        self.base_ubl._ubl_add_tax_scheme(
            {"id": "VAT", "name": "VAT", "type_code": "S"}, root, self.ns
        )
        tax_scheme = root.find(self.ns["cac"] + "TaxScheme")
        self.assertIsNotNone(tax_scheme)
        self.assertEqual(tax_scheme.find(self.ns["cbc"] + "ID").text, "VAT")

    def test_ubl_get_nsmap_namespace(self):
        nsmap, ns = self.base_ubl._ubl_get_nsmap_namespace("Invoice")
        self.assertIn("cac", nsmap)
        self.assertIn("cbc", nsmap)
        self.assertIn("cac", ns)
        self.assertIn("cbc", ns)
