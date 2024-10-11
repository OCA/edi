# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests.common import TransactionCase


class TestBaseUblParse(TransactionCase):
    def test_parse_product_schemeid_gtin(self):
        xml_string = b"""<?xml version="1.0" encoding="UTF-8" ?>
        <Root
            xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
            xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
        >
            <cac:Item>
                <cbc:Description>Acme beeswax</cbc:Description>
                <cbc:Name>beeswax</cbc:Name>
                <cac:StandardItemIdentification>
                    <cbc:ID schemeID="GTIN">6578489</cbc:ID>
                </cac:StandardItemIdentification>
                <cac:SellersItemIdentification>
                    <cbc:ID>17589683</cbc:ID>
                </cac:SellersItemIdentification>
            </cac:Item>
        </Root>
        """
        xml_root = etree.fromstring(xml_string)
        ns = xml_root.nsmap
        product = self.env["base.ubl"].ubl_parse_product(xml_root, ns)
        self.assertEqual(product.get("barcode"), "6578489")
        self.assertEqual(product.get("code"), "17589683")

    def test_parse_product_schemeid_0160(self):
        xml_string = b"""<?xml version="1.0" encoding="UTF-8" ?>
        <Root
            xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
            xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
        >
            <cac:Item>
                <cbc:Description>Acme beeswax</cbc:Description>
                <cbc:Name>beeswax</cbc:Name>
                <cac:StandardItemIdentification>
                    <cbc:ID schemeID="0160">6578489</cbc:ID>
                </cac:StandardItemIdentification>
                <cac:SellersItemIdentification>
                    <cbc:ID>17589683</cbc:ID>
                </cac:SellersItemIdentification>
            </cac:Item>
        </Root>
        """
        xml_root = etree.fromstring(xml_string)
        ns = xml_root.nsmap
        product = self.env["base.ubl"].ubl_parse_product(xml_root, ns)
        self.assertEqual(product.get("barcode"), "6578489")
        self.assertEqual(product.get("code"), "17589683")
