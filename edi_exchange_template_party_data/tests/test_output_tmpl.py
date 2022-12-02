# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


from odoo.addons.edi_oca.tests.common import EDIBackendCommonComponentTestCase


class TestEDIBackendOutputBase(EDIBackendCommonComponentTestCase):
    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        model = cls.env["edi.exchange.template.output"]
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


class TestEDIBackendOutput(TestEDIBackendOutputBase):
    def test_get_party_data(self):
        data = self.tmpl_out2._get_party_data(self.record2, self.env.user.partner_id)
        self.assertEqual(data, {"name": "OdooBot", "identifiers": [], "endpoint": {}})
