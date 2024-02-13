# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import tools
from odoo.exceptions import ValidationError

from odoo.addons.component.exception import NoComponentError
from odoo.addons.edi.tests import common


class Pdf2DataTestCase(common.EDIBackendCommonComponentRegistryTestCase):
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
                "code": "pdf2data",
                "direction": "input",
                "backend_type_id": cls.env.ref("edi_pdf2data.backend_type").id,
            }
        )

    def import_template(self, file="com.amazon.aws.yml"):
        template_yml = tools.file_open(
            file, mode="r", subdir="addons/edi_pdf2data/tests"
        ).read()
        template = self.env["pdf2data.template"].create(
            {"name": "Amazon WS", "exchange_type_id": self.exchange_type.id}
        )
        self.env["pdf2data.template.import.yml"].create(
            {"template_id": template.id, "data": template_yml}
        ).import_data()
        return template

    def test_error_01(self):
        with self.assertRaises(ValidationError):
            self.import_file.import_pdf()

    def test_error_02(self):
        self.import_template()
        with self.assertRaises(NoComponentError):
            self.import_file.import_pdf()

    def test_error_03(self):
        self.import_template("com.amazon.aws-exclude.yml")
        with self.assertRaises(ValidationError):
            self.import_file.import_pdf()

    def test_error_04(self):
        self.import_template("com.amazon.aws-include.yml")
        with self.assertRaises(ValidationError):
            self.import_file.import_pdf()

    def test_check_data(self):
        template = self.import_template()
        template.write(
            {"pdf_file": base64.b64encode(self.file), "pdf_filename": "amazon.pdf"}
        )
        self.assertFalse(template.file_result)
        template.check_pdf()
        self.assertTrue(template.file_result)

    def test_check_data_no_template(self):
        template = self.import_template("com.amazon.aws-include.yml")
        template.write(
            {"pdf_file": base64.b64encode(self.file), "pdf_filename": "amazon.pdf"}
        )
        self.assertFalse(template.file_result)
        template.check_pdf()
        self.assertTrue(template.file_result)
