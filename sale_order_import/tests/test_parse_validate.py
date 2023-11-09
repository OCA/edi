# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from unittest import mock

from lxml import etree

from odoo import exceptions
from odoo.tests.common import Form

from .common import TestCommon


class TestParsingValidation(TestCommon):
    """Mostly unit tests on wizard parsing methods."""

    def test_wrong_import_type(self):
        order_file_data = base64.b64encode(
            b"<?xml version='1.0' encoding='utf-8'?><root><foo>baz</foo></root>"
        )
        order_filename = "test_order.xml"
        expected_error_message = (
            "This file 'test_order.xml' is not recognized as"
            " a PDF file. Please check the file and its extension."
        )

        with self.assertRaisesRegex(exceptions.UserError, expected_error_message):
            with Form(
                self.wiz_model.with_context(default_order_filename=order_filename)
            ) as form:
                form.import_type = "pdf"
                form.order_file = order_file_data

    def test_onchange_validation_xml(self):
        xml_data = base64.b64encode(
            b"<?xml version='1.0' encoding='utf-8'?><root><foo>baz</foo></root>"
        )

        # Simulate bad file handling
        mock_parse_xml = mock.patch.object(type(self.wiz_model), "_parse_xml")

        with Form(
            self.wiz_model.with_context(default_order_filename="test.xml")
        ) as form:
            with mock_parse_xml as mocked:
                mocked.return_value = ("", "I don't like this file")
                with self.assertRaisesRegex(
                    exceptions.UserError, "I don't like this file"
                ):
                    form.import_type = "xml"
                    form.order_file = xml_data
                mocked.assert_called()

        mock_parse_order = mock.patch.object(type(self.wiz_model), "parse_xml_order")

        with Form(
            self.wiz_model.with_context(default_order_filename="test.xml")
        ) as form:
            with mock_parse_order as mocked:
                mocked.return_value = "rfq"
                form.import_type = "xml"
                form.order_file = xml_data
                mocked.assert_called()
                self.assertEqual(form.doc_type, "rfq")

    def test_onchange_validation_pdf(self):
        pdf_data = self.read_test_file("test.pdf", mode="rb", as_b64=True)
        mock_parse_order = mock.patch.object(type(self.wiz_model), "parse_pdf_order")

        with Form(
            self.wiz_model.with_context(default_order_filename="test.pdf")
        ) as form:
            with mock_parse_order as mocked:
                mocked.return_value = "rfq"
                form.import_type = "pdf"
                form.order_file = pdf_data
                mocked.assert_called()
                self.assertEqual(form.doc_type, "rfq")

    def test_parse_xml_bad(self):
        xml_root, error_msg = self.wiz_model._parse_xml("")
        self.assertEqual(xml_root, None)
        self.assertEqual(error_msg, "No data provided")
        xml_root, error_msg = self.wiz_model._parse_xml("something_wrong")
        self.assertEqual(xml_root, None)
        self.assertEqual(error_msg, "This XML file is not XML-compliant")

    def test_parse_xml_unsupported(self):
        xml_data = b"<?xml version='1.0' encoding='utf-8'?><root><foo>baz</foo></root>"
        xml_root, error_msg = self.wiz_model._parse_xml(xml_data)
        self.assertTrue(isinstance(xml_root, etree._Element))
        # Due to parse_xml_order NotImplementedError
        mock_parse_order = mock.patch.object(type(self.wiz_model), "parse_xml_order")
        with mock_parse_order as mocked:
            mocked.side_effect = exceptions.UserError("I don't like this file")
            self.assertTrue(isinstance(xml_root, etree._Element))

    def test_parse_xml_good(self):
        xml_data = b"<?xml version='1.0' encoding='utf-8'?><root><foo>baz</foo></root>"
        mock_parse_order = mock.patch.object(type(self.wiz_model), "parse_xml_order")
        with mock_parse_order as mocked:
            mocked.return_value = "rfq"
            xml_root, error_msg = self.wiz_model._parse_xml(xml_data)
            self.assertTrue(isinstance(xml_root, etree._Element))
            self.assertTrue(error_msg is None)

    def test_parse_pdf_bad(self):
        pdf_data = self.read_test_file("test.pdf", mode="rb", as_b64=True)
        mock_pdf_get_xml_files = mock.patch.object(
            type(self.env["pdf.helper"]), "pdf_get_xml_files"
        )
        with mock_pdf_get_xml_files as mocked:
            mocked.return_value = {}
            with self.assertRaisesRegex(
                exceptions.UserError, "There are no embedded XML file in this PDF file."
            ):
                self.wiz_model.parse_pdf_order(pdf_data)
            mocked.assert_called()

    def test_parse_pdf_good(self):
        pdf_data = self.read_test_file("test.pdf", mode="rb", as_b64=True)
        mock_pdf_get_xml_files = mock.patch.object(
            type(self.env["pdf.helper"]), "pdf_get_xml_files"
        )
        mock_parse_xml_order = mock.patch.object(
            type(self.wiz_model), "parse_xml_order"
        )
        with mock_pdf_get_xml_files as m1, mock_parse_xml_order as m2:
            m1.return_value = {
                "test.pdf": etree.fromstring(
                    b"<?xml version='1.0' encoding='utf-8'?><root><foo>baz</foo></root>"
                )
            }
            fake_parsed_order = {"got": "a wonderful order"}
            m2.return_value = fake_parsed_order
            res = self.wiz_model.parse_pdf_order(pdf_data)
            m1.assert_called()
            m2.assert_called()
            self.assertEqual(res, fake_parsed_order)

    def test_parse_pdf_good_but_no_file(self):
        pdf_data = self.read_test_file("test.pdf", mode="rb", as_b64=True)
        mock_pdf_get_xml_files = mock.patch.object(
            type(self.env["pdf.helper"]), "pdf_get_xml_files"
        )
        mock_parse_xml_order = mock.patch.object(
            type(self.wiz_model), "parse_xml_order"
        )
        with mock_pdf_get_xml_files as m1, mock_parse_xml_order as m2:
            m1.return_value = {
                "test.pdf": etree.fromstring(
                    b"<?xml version='1.0' encoding='utf-8'?><root><foo>baz</foo></root>"
                )
            }
            m2.side_effect = etree.LxmlError("Bad XML sir!")
            expected_msg = (
                "This type of XML RFQ/order is not supported. Did you install "
                "the module to support this XML format?"
            )
            with self.assertRaisesRegex(exceptions.UserError, expected_msg):
                self.wiz_model.parse_pdf_order(pdf_data)
                m1.assert_called()
                m2.assert_called()
            # same w/ UserError catched somewhere else
            m2.side_effect = exceptions.UserError("Something is wrong w/ this file")
            with self.assertRaisesRegex(exceptions.UserError, expected_msg):
                self.wiz_model.parse_pdf_order(pdf_data)
                m1.assert_called()
                m2.assert_called()
