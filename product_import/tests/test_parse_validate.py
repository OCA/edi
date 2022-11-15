# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

import mock
from lxml import etree

from odoo import exceptions
from odoo.tests.common import Form

from .common import TestCommon


class TestParsingValidation(TestCommon):
    """Mostly unit tests on wizard parsing methods."""

    def _mock(self, method_name):
        return mock.patch.object(type(self.wiz_model), method_name)

    def test_onchange_validation_none(self):
        csv_data = base64.b64encode(b"id,name\n,1,Foo")
        with self._mock("_parse_xml") as mocked, Form(self.wiz_model) as form:
            mocked.return_value = "", "Error"
            form.product_file = csv_data
            # no filename, not called
            mocked.assert_not_called()

    def test_onchange_validation_not_supported(self):
        # Check method "_parse_xml" is called
        with self._mock("_parse_xml") as mocked, Form(self.wiz_model) as form:
            mocked.return_value = None, "Error"
            form.product_filename = "test.csv"
            with self.assertRaises(exceptions.UserError):
                form.product_file = "00100000"
            mocked.assert_called()
        # Check method "_unsupported_file_msg" works
        self.assertTrue(self.wiz_model._unsupported_file_msg("fname.omg"))
        # Check correct error is raised
        with Form(self.wiz_model) as form:
            form.product_filename = "test.csv"
            with self.assertRaises(exceptions.UserError) as cm:
                form.product_file = "00100000"
            self.assertEqual(str(cm.exception), "This XML file is not XML-compliant")

    def test_onchange_validation_xml(self):
        xml_data = base64.b64encode(
            b"<?xml version='1.0' encoding='utf-8'?><root><foo>baz</foo></root>"
        )

        with Form(self.wiz_model) as form:
            form.product_filename = "test.xml"
            with self._mock("_parse_xml") as mocked:
                # Simulate bad file handling
                mocked.return_value = ("", "I don't like this file")
                with self.assertRaises(exceptions.UserError) as cm:
                    form.product_file = xml_data
                self.assertEqual(str(cm.exception), "I don't like this file")
                mocked.assert_called()

        with Form(self.wiz_model) as form:
            form.product_filename = "test.xml"
            with self._mock("parse_xml_catalogue") as mocked:
                mocked.return_value = None
                form.product_file = xml_data
                mocked.assert_called()

    def test_parse_xml_bad(self):
        xml_root, error_msg = self.wiz_model._parse_xml("")
        self.assertIsNone(xml_root)
        self.assertEqual(error_msg, "No data provided")
        xml_root, error_msg = self.wiz_model._parse_xml("something_wrong")
        self.assertIsNone(xml_root)
        self.assertEqual(error_msg, "This XML file is not XML-compliant")

    def test_parse_xml_unsupported(self):
        xml_data = b"<?xml version='1.0' encoding='utf-8'?><root><foo>baz</foo></root>"
        xml_root, error_msg = self.wiz_model._parse_xml(xml_data)
        self.assertIsInstance(xml_root, etree._Element)
        # Due to parse_xml NotImplementedError
        self.assertEqual(error_msg, "Unsupported XML document")
        with self._mock("parse_xml_catalogue") as mocked:
            mocked.side_effect = exceptions.UserError("I don't like this file")
            self.assertTrue(isinstance(xml_root, etree._Element))
            self.assertEqual(error_msg, "Unsupported XML document")

    def test_parse_xml_good(self):
        xml_data = b"<?xml version='1.0' encoding='utf-8'?><root><foo>baz</foo></root>"
        with self._mock("parse_xml_catalogue") as mocked:
            mocked.return_value = "catalogue"
            xml_root, error_msg = self.wiz_model._parse_xml(xml_data)
            self.assertIsInstance(xml_root, etree._Element)
            self.assertIsNone(error_msg)
