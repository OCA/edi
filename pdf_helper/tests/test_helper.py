# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import os

from lxml import etree

from odoo.tests.common import BaseCase, TransactionCase

from odoo.addons.pdf_helper.utils import PDFParser


def read_test_file(filename, mode="r"):
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path, mode) as thefile:
        return thefile.read()


# NOTE: this class could use a bare `unittest.TestCase` as base
# but w/out TreeCase Odoo won't load these tests.
class TestPDFHelperUtils(BaseCase):
    def test_parse_xml(self):
        pdf_content = read_test_file("pdf_with_xml_test.pdf", mode="rb")
        res = PDFParser(pdf_content).get_xml_files()
        fname, xml_root = tuple(res.items())[0]
        self.assertEqual(fname, "factur-x.xml")
        self.assertTrue(isinstance(xml_root, etree._Element))


class TestPDFHelper(TransactionCase):
    def test_get_xml(self):
        pdf_content = read_test_file("pdf_with_xml_test.pdf", mode="rb")
        res = self.env["pdf.helper"].pdf_get_xml_files(pdf_content)
        fname, xml_root = tuple(res.items())[0]
        self.assertEqual(fname, "factur-x.xml")
        self.assertTrue(isinstance(xml_root, etree._Element))

    def test_get_xml_fail(self):
        with self.assertLogs(
            "odoo.addons.pdf_helper.models.helper", level="ERROR"
        ) as log_catcher:
            self.env["pdf.helper"].pdf_get_xml_files(b"")
            self.assertIn(
                "PDF file parsing failed: Cannot read an empty file",
                log_catcher.output[0],
            )

    def test_embed_xml(self):
        pdf_content = read_test_file("pdf_with_xml_test.pdf", mode="rb")
        filename = "test"
        xml = b"<root>test</root>"
        newpdf_content = self.env["pdf.helper"].pdf_embed_xml(
            pdf_content, filename, xml
        )
        attachments = self.env["pdf.helper"].pdf_get_xml_files(newpdf_content)
        self.assertTrue(filename in attachments)
        etree_content = attachments[filename]
        self.assertEqual(xml, etree.tostring(etree_content))
