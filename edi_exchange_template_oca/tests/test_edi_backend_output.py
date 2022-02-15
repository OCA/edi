# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import base64

from lxml import etree

from odoo.addons.edi_oca.tests.common import EDIBackendCommonComponentTestCase


class TestEDIBackendOutputBase(EDIBackendCommonComponentTestCase):
    @classmethod
    def _setup_records(cls):
        res = super()._setup_records()
        cls.type_out1 = cls._create_exchange_type(
            name="Template output 1",
            direction="output",
            code="test_type_out1",
            exchange_file_ext="txt",
            exchange_filename_pattern="{record.ref}-{type.code}-{dt}",
        )
        model = cls.env["edi.exchange.template.output"]
        qweb_tmpl = cls.env["ir.ui.view"].create(
            {
                "type": "qweb",
                "key": "edi_exchange.test_output1",
                "arch": """
            <t t-name="edi_exchange.test_output1">
                <t t-esc="record.ref" /> - <t t-esc="record.name" />
            </t>
            """,
            }
        )
        cls.tmpl_out1 = model.create(
            {
                "code": "edi.output.generate.demo_backend.test_type_out1",
                "name": "Out 1",
                "backend_type_id": cls.backend.backend_type_id.id,
                "type_id": cls.type_out1.id,
                "template_id": qweb_tmpl.id,
                "output_type": "txt",
            }
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
            "type_id": cls.type_out1.id,
        }
        cls.record1 = cls.backend.create_record("test_type_out1", vals)

        cls.type_out2 = cls._create_exchange_type(
            name="Template output 2",
            direction="output",
            code="test_type_out2",
            exchange_file_ext="xml",
            exchange_filename_pattern="{record.ref}-{type.code}-{dt}",
        )
        qweb_tmpl = cls.env["ir.ui.view"].create(
            {
                "type": "qweb",
                "key": "edi_exchange.test_output2",
                "arch": """
            <t t-name="edi_exchange.test_output2">
                <t t-name="edi_exchange.test_output2">
                    <Record t-att-ref="record.ref">
                        <Name t-esc="record.name" />
                        <Custom t-att-bit="custom_bit" t-esc="baz"/>
                    </Record>
                </t>
            </t>
            """,
            }
        )
        cls.tmpl_out2 = model.create(
            {
                "code": "edi.output.generate.demo_backend.test_type_out2",
                "name": "Out 2",
                "backend_type_id": cls.backend.backend_type_id.id,
                "type_id": cls.type_out2.id,
                "template_id": qweb_tmpl.id,
                "output_type": "xml",
                "code_snippet": """
foo = "custom_var"
baz = 2
result = {"custom_bit": foo, "baz": baz}
                """,
            }
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
            "type_id": cls.type_out2.id,
        }
        cls.record2 = cls.backend.create_record("test_type_out2", vals)
        cls.type_out3 = cls._create_exchange_type(
            name="Template output 3",
            direction="output",
            code="test_type_out3",
            exchange_file_ext="xml",
            exchange_filename_pattern="{record.id}-{type.code}-{dt}",
        )
        cls.report = cls.env.ref("web.action_report_externalpreview")
        cls.tmpl_out3 = model.create(
            {
                "code": "edi.output.generate.demo_backend.test_type_out3",
                "name": "Out 3",
                "backend_type_id": cls.backend.backend_type_id.id,
                "type_id": cls.type_out3.id,
                "generator": "report",
                "report_id": cls.report.id,
                "output_type": "pdf",
                "code_snippet": """
result = {"res_ids": record.ids}
                        """,
            }
        )
        company = cls.env.ref("base.main_company")
        vals = {
            "model": company._name,
            "res_id": company.id,
            "type_id": cls.type_out2.id,
        }
        cls.record3 = cls.backend.create_record("test_type_out3", vals)
        return res


# TODO: add more unit tests
class TestEDIBackendOutput(TestEDIBackendOutputBase):
    def test_get_template(self):
        self.assertEqual(
            self.backend._get_output_template(self.record1), self.tmpl_out1
        )
        self.assertEqual(
            self.backend._get_output_template(self.record2), self.tmpl_out2
        )
        self.assertEqual(
            self.backend._get_output_template(self.record2, code=self.tmpl_out1.code),
            self.tmpl_out1,
        )

    def test_generate_file(self):
        output = self.backend.exchange_generate(self.record1)
        expected = "{0.ref} - {0.name}".format(self.partner)
        self.assertEqual(output.strip(), expected)
        file_content = base64.b64decode(self.record1.exchange_file).decode()
        self.assertEqual(file_content.strip(), expected)
        output = self.backend.exchange_generate(self.record2)
        doc = etree.fromstring(output)
        self.assertEqual(doc.tag, "Record")
        self.assertEqual(doc.attrib, {"ref": self.partner.ref})
        self.assertEqual(doc.getchildren()[0].tag, "Name")
        self.assertEqual(doc.getchildren()[0].text, self.partner.name)
        self.assertEqual(doc.getchildren()[1].tag, "Custom")
        self.assertEqual(doc.getchildren()[1].text, "2")
        self.assertEqual(doc.getchildren()[1].attrib, {"bit": "custom_var"})

    def test_generate_file_report(self):
        output = self.backend.exchange_generate(self.record3)
        self.assertTrue(output)
        self.assertEqual(
            self.report._render([self.record3.res_id])[0].strip().decode("UTF-8"),
            output.strip(),
        )
