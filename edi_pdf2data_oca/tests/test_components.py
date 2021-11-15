# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

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

        template = tools.file_open(
            "com.amazon.aws.yml", mode="r", subdir="addons/edi_pdf2data/tests",
        ).read()
        template_type = cls.env["pdf2data.template.type"].create(
            {"code": "invoice.demo", "name": "Standard invoice"}
        )
        cls.template = cls.env["pdf2data.template"].create(
            {
                "pdf2data_template_yml": template,
                "name": "Amazon WS",
                "type_id": template_type.id,
            }
        )

        class DemoComponent(Component):
            _inherit = "edi.component.process_data.mixin"
            _name = "edi.component.process_data.demo"
            _usage = "process_data"
            _backend_type = "import_data"
            _exchange_type = None
            _process_type = "invoice.demo"

            def process_data(self, data, template, file):
                record = self.env.user.partner_id
                self.exchange_record.write({"model": record._name, "res_id": record.id})

            def preview_data(self, data, template):
                return data

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
        self.assertFalse(self.template.file_processed_result)
        self.template.check_pdf()
        self.assertTrue(self.template.file_result)
        self.assertTrue(self.template.file_processed_result)
        self.assertIn(self.template.file_result, self.template.file_processed_result)
        # Some html items have been added, so, we check that the data is contained
