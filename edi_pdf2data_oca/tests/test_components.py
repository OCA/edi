# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

import yaml

from odoo import tools

from odoo.addons.component.core import Component
from odoo.addons.edi.tests import common


class Pdf2DataComponentTestCase(common.EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.file = tools.file_open(
            "AmazonWebServices.pdf", mode="rb", subdir="addons/edi_pdf2data/tests",
        ).read()
        cls._load_module_components(cls, "edi")
        cls._load_module_components(cls, "edi_pdf2data")
        cls.import_file = cls.env["pdf2data.import"].create(
            {
                "pdf_file": base64.b64encode(cls.file),
                "pdf_file_name": "AmazonWebServices.pdf",
            }
        )

        cls.exchange_type = cls.env["edi.exchange.type"].create(
            {
                "name": "Test CSV exchange",
                "code": "invoice.demo",
                "direction": "input",
                "backend_type_id": cls.env.ref("edi_pdf2data.backend_type").id,
            }
        )
        template_yml = tools.file_open(
            "com.amazon.aws.yml", mode="r", subdir="addons/edi_pdf2data/tests",
        ).read()
        cls.template = cls.env["pdf2data.template"].create(
            {"name": "Amazon WS", "exchange_type_id": cls.exchange_type.id}
        )
        cls.env["pdf2data.template.import.yml"].create(
            {"template_id": cls.template.id, "data": template_yml}
        ).import_data()

        class DemoComponent(Component):
            _name = "edi.component.process_data.demo"
            _inherit = "edi.input.process.pdf2data.abstract"
            _exchange_type = "invoice.demo"

            def process_data(self, data, template):
                record = self.env.user.partner_id
                self.exchange_record.write({"model": record._name, "res_id": record.id})

        cls._build_components(
            cls, DemoComponent,
        )

    def test_import(self):
        action = self.import_file.import_pdf()
        self.assertEqual(
            self.env.user.partner_id,
            self.env[action["res_model"]].browse(action["res_id"]),
        )

    def test_preview(self):
        self.template.write(
            {
                "pdf_file": base64.b64encode(self.file),
                "pdf_filename": "AmazonWebServices.pdf",
            }
        )
        self.assertFalse(self.template.file_result)
        self.template.check_pdf()
        self.assertTrue(self.template.file_result)
        self.assertTrue(
            isinstance(
                yaml.load(self.template.file_result, Loader=yaml.SafeLoader), dict
            )
        )
        # Some html items have been added, so, we check that the data is contained
