# Copyright 2018 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import os

import mock
from lxml import etree

from odoo import exceptions
from odoo.tests.common import Form, SavepointCase


class TestOrderImport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.wiz_model = cls.env["sale.order.import"]
        cls.partner = cls.env["res.partner"].create({"name": "SO Test"})
        cls.parsed_order = {
            "partner": {"email": "deco.addict82@example.com"},
            "date": "2018-08-14",
            "order_ref": "TEST1242",
            "lines": [
                {
                    "product": {"code": "FURN_8888"},
                    "qty": 2,
                    "uom": {"unece_code": "C62"},
                    "price_unit": 12.42,
                }
            ],
            "chatter_msg": [],
            "doc_type": "rfq",
        }

    def read_test_file(self, filename, mode="r"):
        path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
        with open(path, mode) as thefile:
            return thefile.read()

    def test_order_import(self):
        order = self.wiz_model.create_order(self.parsed_order, "pricelist")
        self.assertEqual(order.client_order_ref, self.parsed_order["order_ref"])
        self.assertEqual(
            order.order_line[0].product_id.default_code,
            self.parsed_order["lines"][0]["product"]["code"],
        )
        self.assertEqual(int(order.order_line[0].product_uom_qty), 2)
        # Now update the order
        parsed_order_up = {
            "partner": {"email": "agrolait@yourcompany.example.com"},
            "date": "2018-08-14",
            "order_ref": "TEST1242",
            "lines": [
                {
                    "product": {"code": "FURN_8888"},
                    "qty": 3,
                    "uom": {"unece_code": "C62"},
                    "price_unit": 12.42,
                },
                {
                    "product": {"code": "FURN_9999"},
                    "qty": 1,
                    "uom": {"unece_code": "C62"},
                    "price_unit": 1.42,
                },
            ],
            "chatter_msg": [],
            "doc_type": "rfq",
        }
        self.wiz_model.update_order_lines(parsed_order_up, order, "pricelist")
        self.assertEqual(len(order.order_line), 2)
        self.assertEqual(int(order.order_line[0].product_uom_qty), 3)

    def test_onchange_validation_none(self):
        csv_data = base64.b64encode(b"id,name\n,1,Foo")
        with Form(self.wiz_model) as form:
            form.order_file = csv_data
            # no filename, no party
            self.assertFalse(form.csv_import)
            self.assertFalse(form.doc_type)

    def test_onchange_validation_not_supported(self):
        # Just test is not broken
        self.assertTrue(self.wiz_model._unsupported_file_msg("fname.omg"))
        # Test it gets called (cannot do it w/ Form)
        mock_file_msg = mock.patch.object(type(self.wiz_model), "_unsupported_file_msg")
        with mock_file_msg as mocked:
            with Form(self.wiz_model) as form:
                form.order_filename = "test.omg"
                form.order_file = "00100000"
                self.assertFalse(form.csv_import)
                self.assertFalse(form.doc_type)
                mocked.assert_called()

    def test_onchange_validation_csv(self):
        csv_data = base64.b64encode(b"id,name\n,1,Foo")

        with Form(self.wiz_model) as form:
            form.partner_id = self.partner  # required by the view if CSV is set
            form.order_filename = "test.csv"
            form.order_file = csv_data
            self.assertTrue(form.csv_import)
            self.assertFalse(form.doc_type)

    def test_onchange_validation_xml(self):
        xml_data = base64.b64encode(
            b"<?xml version='1.0' encoding='utf-8'?><root><foo>baz</foo></root>"
        )

        # Simulate bad file handling
        mock_parse_xml = mock.patch.object(type(self.wiz_model), "_parse_xml")

        with Form(self.wiz_model) as form:
            form.order_filename = "test.xml"
            with mock_parse_xml as mocked:
                mocked.return_value = ("", "I don't like this file")
                with self.assertRaisesRegex(
                    exceptions.UserError, "I don't like this file"
                ):
                    form.order_file = xml_data
                mocked.assert_called()

        mock_parse_order = mock.patch.object(type(self.wiz_model), "parse_xml_order")

        with Form(self.wiz_model) as form:
            form.order_filename = "test.xml"
            with mock_parse_order as mocked:
                mocked.return_value = "rfq"
                form.order_file = xml_data
                mocked.assert_called()
                self.assertFalse(form.csv_import)
                self.assertEqual(form.doc_type, "rfq")

    def test_onchange_validation_pdf(self):
        pdf_data = base64.b64encode(self.read_test_file("test.pdf", mode="rb"))
        mock_parse_order = mock.patch.object(type(self.wiz_model), "parse_pdf_order")

        with Form(self.wiz_model) as form:
            # form.partner_id = self.partner  # required by the view if CSV is set
            form.order_filename = "test.pdf"
            with mock_parse_order as mocked:
                mocked.return_value = "rfq"
                form.order_file = pdf_data
                mocked.assert_called()
                self.assertFalse(form.csv_import)
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
        self.assertEqual(error_msg, "Unsupported XML document")
        mock_parse_order = mock.patch.object(type(self.wiz_model), "parse_xml_order")
        with mock_parse_order as mocked:
            mocked.side_effect = exceptions.UserError("I don't like this file")
            self.assertTrue(isinstance(xml_root, etree._Element))
            self.assertEqual(error_msg, "Unsupported XML document")

    def test_parse_xml_good(self):
        xml_data = b"<?xml version='1.0' encoding='utf-8'?><root><foo>baz</foo></root>"
        mock_parse_order = mock.patch.object(type(self.wiz_model), "parse_xml_order")
        with mock_parse_order as mocked:
            mocked.return_value = "rfq"
            xml_root, error_msg = self.wiz_model._parse_xml(xml_data)
            self.assertTrue(isinstance(xml_root, etree._Element))
            self.assertTrue(error_msg is None)
