# Copyright 2025 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import mute_logger
from odoo.tests.common import TransactionCase


class TestUblCheckXmlSchema(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_ubl = cls.env["base.ubl"]
        # Example: invalid XML (missing required UBLVersionID)
        cls.invalid_xml = b"""
        <Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
                 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
            <cbc:ID>F123</cbc:ID>
        </Invoice>
        """

    def test_ubl_check_xml_schema_valid(self):
        with mock.patch(
            "odoo.addons.base_ubl.models.ubl.etree.XMLSchema",
            return_value=mock.MagicMock(),
            spec=etree.XMLSchema,
        ):
            self.assertTrue(
                self.base_ubl._ubl_check_xml_schema(b"<whatever />", "Invoice", "2.1")
            )

    @mute_logger("odoo.addons.base_ubl.models.ubl")
    def test_ubl_check_xml_schema_invalid(self):
        with self.assertRaises(UserError):
            self.base_ubl._ubl_check_xml_schema(self.invalid_xml, "Invoice", "2.1")

    def test_ubl_get_nsmap_namespace(self):
        nsmap, ns = self.base_ubl._ubl_get_nsmap_namespace("Invoice")
        self.assertIn("cac", nsmap)
        self.assertIn("cbc", nsmap)
        self.assertIn("cac", ns)
        self.assertIn("cbc", ns)
