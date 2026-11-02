# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from base64 import b64encode
from os import path

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form, new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestBaseImportPdfByTemplate(BaseCommon):
    """The template is built here instead of reusing the demo one because tests
    are run without demo data."""

    @classmethod
    def _field(cls, model, name):
        return cls.env["ir.model.fields"]._get(model, name)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(cls.env, login="test-user")
        # Archive any other res.partner template (e.g. the demo one) so that the
        # auto-detection can only match the one created below.
        cls.env["base.import.pdf.template"].search(
            [("model", "=", "res.partner")]
        ).active = False
        country_es = cls.env.ref("base.es")
        cls.env["res.partner.industry"].create({"name": "Food"})
        type_other = cls.env["ir.model.fields.selection"].search(
            [
                ("field_id", "=", cls._field("res.partner", "type").id),
                ("value", "=", "other"),
            ]
        )
        cls.template = cls.env["base.import.pdf.template"].create(
            {
                "name": "Partner Template",
                "model_id": cls.env["ir.model"]._get("res.partner").id,
                "child_field_id": cls._field("res.partner", "child_ids").id,
                "auto_detect_pattern": "Test partner info.*",
                "line_ids": [
                    Command.create(
                        {
                            "related_model": "header",
                            "field_id": cls._field("res.partner", "name").id,
                            "pattern": r"Partner name:[\n] [\n](.*)",
                        }
                    ),
                    Command.create(
                        {
                            "related_model": "header",
                            "field_id": cls._field("res.partner", "country_id").id,
                            "search_field_id": cls._field("res.country", "code").id,
                            "pattern": r"[A-Z].* [(]([A-Z]{1,2})[)][\n]Industry",
                        }
                    ),
                    Command.create(
                        {
                            "related_model": "header",
                            "field_id": cls._field("res.partner", "industry_id").id,
                            "search_field_id": cls._field(
                                "res.partner.industry", "name"
                            ).id,
                            "pattern": r"Industry:[\n] [\n](.*)",
                        }
                    ),
                    Command.create(
                        {
                            "related_model": "header",
                            "field_id": cls._field("res.partner", "user_id").id,
                            "value_type": "fixed",
                            "fixed_value": f"{cls.user._name},{cls.user.id}",
                        }
                    ),
                    Command.create(
                        {
                            "related_model": "header",
                            "field_id": cls._field("res.partner", "ref").id,
                            "value_type": "fixed",
                            "fixed_value_char": "fixed-ref",
                        }
                    ),
                    # Children must be created as addresses: in a "contact" the
                    # address fields are invisible in the res.partner form view.
                    Command.create(
                        {
                            "related_model": "lines",
                            "field_id": cls._field("res.partner", "type").id,
                            "value_type": "fixed",
                            "fixed_value_selection": type_other.id,
                        }
                    ),
                    Command.create(
                        {
                            "related_model": "lines",
                            "field_id": cls._field("res.partner", "name").id,
                            "sequence": 0,
                            "pattern": r"(.*),.*,",
                        }
                    ),
                    Command.create(
                        {
                            "related_model": "lines",
                            "field_id": cls._field("res.partner", "street").id,
                            "sequence": 1,
                            "pattern": r".*,(.*),",
                        }
                    ),
                    Command.create(
                        {
                            "related_model": "lines",
                            "field_id": cls._field("res.partner", "country_id").id,
                            "search_field_id": cls._field("res.country", "code").id,
                            "sequence": 2,
                            "pattern": r".*,.*, [A-Z].*[(]([A-Z]{1,2})[)]",
                            "log_distinct_value": True,
                            "default_value": f"{country_es._name},{country_es.id}",
                        }
                    ),
                ],
            }
        )
        cls.name_line = cls.template.line_ids.filtered(
            lambda x: x.related_model == "header" and x.field_name == "name"
        )
        cls.country_line = cls.template.line_ids.filtered(
            lambda x: x.related_model == "lines" and x.field_name == "country_id"
        )

    def _data_file(self, filename, encoding=None):
        filename = "data/" + filename
        mode = "rt" if encoding else "rb"
        with open(path.join(path.dirname(__file__), filename), mode) as file:
            data = file.read()
            if encoding:
                data = data.encode(encoding)
            return b64encode(data)

    def _create_ir_attachment(self, filename):
        return self.env["ir.attachment"].create(
            {
                "name": filename,
                "datas": self._data_file(filename),
            }
        )

    def _create_wizard_base_import_pdf_upload(self, attachment):
        wizard = self.env["wizard.base.import.pdf.upload"].create(
            {
                "model": "res.partner",
                "attachment_ids": attachment.ids,
            }
        )
        # We need to set is_company so that the industry_id field is visible
        # in the res.partner form view.
        return wizard.with_context(default_is_company=True)

    def _get_attachments_from_record(self, record):
        return self.env["ir.attachment"].search(
            [("res_model", "=", record._name), ("res_id", "=", record.id)]
        )

    def test_wizard_base_import_pdf_preview(self):
        wizard_form = Form(
            self.env["wizard.base.import.pdf.preview"].with_context(
                default_template_id=self.template
            )
        )
        wizard_form.data_file = self._data_file("res-partner.pdf")
        self.assertEqual(wizard_form.total_pages, 1)
        self.assertIn("Test partner info", wizard_form.data)

    def test_wizard_base_import_pdf_by_template_01(self):
        attachment = self._create_ir_attachment("res-partner.pdf")
        wizard = self._create_wizard_base_import_pdf_upload(attachment)
        res = wizard.action_process()
        record = self.env[res["res_model"]].browse(res["res_id"])
        self.assertEqual(record._name, "res.partner")
        self.assertEqual(record.name, "Test partner")
        self.assertEqual(record.country_id.code, "ES")
        self.assertEqual(record.industry_id.name, "Food")
        self.assertEqual(record.user_id, self.user)
        self.assertEqual(record.ref, "fixed-ref")
        self.assertEqual(len(record.child_ids), 3)
        self.assertEqual(set(record.child_ids.mapped("type")), {"other"})
        child_1 = record.child_ids.filtered(lambda x: x.name == "Child 1")
        self.assertEqual(child_1.street, "Address 1")
        self.assertEqual(child_1.country_id.code, "ES")
        child_2 = record.child_ids.filtered(lambda x: x.name == "Child 2")
        self.assertEqual(child_2.street, "Address 2")
        self.assertEqual(child_2.country_id.code, "ES")
        child_3 = record.child_ids.filtered(lambda x: x.name == "Child 3")
        self.assertEqual(child_3.street, "Address 3")
        self.assertEqual(child_3.country_id.code, "ES")
        # Child 2 has been set with France instead of Spain
        # Child 3 has been set with Portgual instead of Spain
        self.assertIn("France", record.message_ids.body)
        self.assertIn("Portugal", record.message_ids.body)
        self.assertIn("Spain", record.message_ids.body)
        self.assertNotIn("Child 1", record.message_ids.body)
        self.assertIn("Child 2", record.message_ids.body)
        self.assertIn("Child 3", record.message_ids.body)
        # # Attachment
        attachments = self._get_attachments_from_record(record)
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments.name, "res-partner.pdf")

    def test_wizard_base_import_pdf_by_template_02(self):
        self.country_line.log_distinct_value = False
        # Change PT country code to check default_value
        self.env.ref("base.pt").code = "OLD-PT"
        attachment = self._create_ir_attachment("res-partner.pdf")
        wizard = self._create_wizard_base_import_pdf_upload(attachment)
        res = wizard.action_process()
        record = self.env[res["res_model"]].browse(res["res_id"])
        self.assertEqual(record._name, "res.partner")
        self.assertEqual(record.name, "Test partner")
        self.assertEqual(record.country_id.code, "ES")
        self.assertEqual(record.industry_id.name, "Food")
        self.assertEqual(record.user_id, self.user)
        self.assertEqual(record.ref, "fixed-ref")
        self.assertEqual(len(record.child_ids), 3)
        child_1 = record.child_ids.filtered(lambda x: x.name == "Child 1")
        self.assertEqual(child_1.street, "Address 1")
        self.assertEqual(child_1.country_id.code, "ES")
        child_2 = record.child_ids.filtered(lambda x: x.name == "Child 2")
        self.assertEqual(child_2.street, "Address 2")
        self.assertEqual(child_2.country_id.code, "FR")
        child_3 = record.child_ids.filtered(lambda x: x.name == "Child 3")
        self.assertEqual(child_3.street, "Address 3")
        self.assertEqual(child_3.country_id.code, "ES")
        # The fixed values defined for the header are not applied to the child
        # lines, so no error is logged (the main model and the child one are the
        # same in this template).
        self.assertFalse(any(record.child_ids.mapped("ref")))
        self.assertFalse(record.message_ids)

    def test_wizard_base_import_pdf_by_template_error(self):
        self.name_line.write({"pattern": "TEST"})
        attachment = self._create_ir_attachment("res-partner.pdf")
        wizard = self._create_wizard_base_import_pdf_upload(attachment)
        with self.assertRaises(UserError):
            wizard.action_process()  # name is a required field
