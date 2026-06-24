# Copyright 2026 Binhex
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import shutil
import tempfile

from odoo.tests.common import TransactionCase


class CommonEdiLocalCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, lang=False)
        )
        cls.edi_local_model = cls.env["edi.local"]
        cls.edi_local_line_model = cls.env["edi.local.line"]
        cls.edi_local_header_model = cls.env["edi.local.header"]
        cls.attachment_model = cls.env["ir.attachment"].sudo()
        cls.partner_model = cls.env.ref("base.model_res_partner")
        cls.child_field = cls.env["ir.model.fields"].search(
            [
                ("model", "=", "res.partner"),
                ("name", "=", "child_ids"),
            ],
            limit=1,
        )
        cls.header = cls.env.ref("edi_local.edi_local_type_header_gen")
        partner_values = {
            "name": "EDI Parent",
            "email": "edi.parent@example.com",
            "child_ids": [
                (0, 0, {"name": "EDI Child 1"}),
                (0, 0, {"name": "EDI Child 2"}),
            ],
        }
        if "split_method" in cls.env["res.partner"]._fields:
            partner_values["split_method"] = "equal"
            for child_command in partner_values["child_ids"]:
                child_command[2]["split_method"] = "equal"
        cls.partner = cls.env["res.partner"].create(partner_values)
        cls.output_dir = tempfile.mkdtemp(prefix="edi_local_out_")
        cls.input_dir = tempfile.mkdtemp(prefix="edi_local_in_")
        cls._sequence_index = 0

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.output_dir, ignore_errors=True)
        shutil.rmtree(cls.input_dir, ignore_errors=True)
        super().tearDownClass()

    @classmethod
    def _new_sequence(cls):
        cls._sequence_index += 1
        return cls.env["ir.sequence"].create(
            {
                "name": f"EDI Local Test {cls._sequence_index}",
                "code": f"edi.local.test.{cls._sequence_index}",
                "prefix": f"EDI{cls._sequence_index:02d}-",
                "padding": 3,
            }
        )

    @classmethod
    def _create_local(cls, **overrides):
        values = {
            "name": "EDI Local Test",
            "model_id": cls.partner_model.id,
            "domain": f"[('id', '=', {cls.partner.id})]",
            "file_type": "txt",
            "type": "out",
            "enabled": False,
            "override_file": True,
            "sequence_id": cls._new_sequence().id,
            "dir_file": cls.output_dir,
        }
        values.update(overrides)
        return cls.edi_local_model.create(values)

    @classmethod
    def _create_line(cls, local, **overrides):
        values = {
            "edi_local_id": local.id,
            "name": "name",
            "description": "Name",
            "type": "header",
            "type_header": cls.header.id,
            "sequence": 10,
            "start": 1,
            "size": 8,
            "type_data": "alphanumeric",
            "is_required": True,
            "value": "result = record.name",
        }
        values.update(overrides)
        return cls.edi_local_line_model.create(values)

    def setUp(self):
        super().setUp()
        self.edi_local_model.search([]).write({"enabled": False})
