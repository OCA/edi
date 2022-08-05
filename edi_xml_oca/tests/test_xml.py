# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.tests.common import SavepointComponentCase

from .common import XMLTestCaseMixin

TEST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<xs:element
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    name="shoesize"
    type="shoetype"
    />
"""


class XMLTestCase(SavepointComponentCase, XMLTestCaseMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls.env.ref("edi_oca.demo_edi_backend")
        cls.handler = cls.backend._find_component(
            cls.backend._name,
            ["edi.xml"],
            work_ctx={"schema_path": "edi_xml_oca:tests/fixtures/Test.xsd"},
        )

    def test_xml_schema_fail(self):
        with self.assertRaises(ValueError):
            self.backend._find_component(
                self.backend._name, ["edi.xml"], work_ctx={"schema_path": "Nothing"}
            )
        with self.assertRaises(AttributeError):
            self.backend._find_component(
                self.backend._name, ["edi.xml"], work_ctx={"no_schema": "Nothing"}
            )

    def test_xml(self):
        data = self.handler.parse_xml(TEST_XML)
        self.assertEqual(
            data,
            {
                "@abstract": False,
                "@name": "shoesize",
                "@nillable": False,
                "@type": "shoetype",
                "@xmlns:xs": "http://www.w3.org/2001/XMLSchema",
            },
        )
