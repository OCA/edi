# Copyright 2026 Binhex
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from pathlib import Path
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.edi_local.utils import (
    get_notification,
    is_alphanumeric,
    is_date,
    is_numeric,
)

from .common import CommonEdiLocalCase


@tagged("-at_install", "post_install")
class TestEdiLocal(CommonEdiLocalCase):
    def test_available_variables_is_computed(self):
        local = self._create_local()

        self.assertIn("#  - env:", local.available_variables)
        self.assertIn("UserError", local.available_variables)
        self.assertIn("result", local.available_variables)

    def test_generate_file_txt_accepts_empty_optional_values(self):
        local = self._create_local()
        self._create_line(
            local,
            name="fixed_value",
            value="result = 'HDR'",
            size=3,
        )
        self._create_line(
            local,
            name="optional_empty",
            value="result = ''",
            start=4,
            size=1,
            is_required=False,
            fill_value=False,
        )

        files = local.with_context(test_generate_file=True).generate_file_txt(
            self.partner
        )

        self.assertEqual(len(files), 1)
        self.assertEqual(next(iter(files[0].values())), "HDR\n")

    def test_generate_file_returns_success_notification(self):
        local = self._create_local(enabled=True)
        self._create_line(
            local,
            name="partner_name",
            value="result = record.name",
            size=10,
        )

        with patch.object(
            type(local), "valid_dir_file", autospec=True, return_value=True
        ), patch.object(type(local), "_post_generate_file", autospec=True):
            result = local.generate_file()

        self.assertEqual(result["params"]["type"], "success")
        generated_path = Path(local.files_generated)
        self.assertTrue(generated_path.exists())
        self.assertEqual(generated_path.read_text(encoding="utf-8"), "EDI Parent\n")

    def test_generate_file_cron_passes_context_to_generate_file(self):
        local = self._create_local(enabled=True)
        self._create_line(local, value="result = 'HDR'", size=3)

        with patch.object(type(local), "generate_file", autospec=True) as mocked:
            self.edi_local_model.with_context(
                lang=self.env.user.lang
            ).generate_file_cron()

        self.assertEqual(mocked.call_count, 1)
        generated_local = mocked.call_args.args[0]
        self.assertEqual(generated_local.ids, local.ids)
        self.assertTrue(generated_local.env.context["generate_with_cron"])
        self.assertEqual(generated_local.env.context["lang"], self.env.user.lang)

    def test_generate_file_cron_posts_error_message(self):
        local = self._create_local(enabled=True)
        self._create_line(
            local,
            name="department",
            value="raise UserError(_('Missing department for %s') % record.name)",
            size=10,
        )

        self.edi_local_model.generate_file_cron()
        self.env.flush_all()
        local.invalidate_recordset(["message_ids"])

        self.assertTrue(local.message_ids)
        body = local.message_ids.sorted("id")[-1].body
        self.assertIn("department", body)
        self.assertIn("Missing department for EDI Parent", body)

    def test_read_files_by_directory_and_parse_import_file(self):
        local = self._create_local(
            type="in",
            dir_import_file=self.input_dir,
            field_id=self.child_field.id,
        )
        self._create_line(
            local,
            name="parent_name",
            type="header",
            value="",
            start=4,
            size=4,
            is_required=False,
        )
        self._create_line(
            local,
            name="name",
            type="line",
            value="",
            start=4,
            size=4,
            is_required=False,
        )
        Path(self.input_dir, "records.txt").write_text("GENALFA\n", encoding="utf-8")
        Path(self.input_dir, "ignore.csv").write_text("NOPE\n", encoding="utf-8")

        local.read_files_by_directory()
        values = local.read_import_file_txt()

        self.assertEqual(local.attachment_ids.mapped("name"), ["records.txt"])
        self.assertEqual(values[0]["gen"]["parent_name"], "ALFA")
        self.assertEqual(len(values[0]["child_ids"]), 1)
        self.assertEqual(values[0]["child_ids"][0][2]["name"], "ALFA")

    def test_read_import_file_requires_attachment(self):
        local = self._create_local(
            type="in",
            enabled=True,
            dir_import_file=False,
            field_id=self.child_field.id,
        )
        self._create_line(
            local,
            name="name",
            type="header",
            value="",
            start=1,
            size=3,
            is_required=False,
        )

        with self.assertRaisesRegex(
            ValidationError,
            "No file was detected|No se detectó ningún archivo",
        ):
            local.read_import_file()

    def test_read_import_file_returns_warning_notification(self):
        local = self._create_local(
            type="in",
            enabled=True,
            dir_import_file=self.input_dir,
            field_id=self.child_field.id,
        )
        self._create_line(
            local,
            name="parent_name",
            type="header",
            value="",
            start=4,
            size=4,
            is_required=False,
        )
        self._create_line(
            local,
            name="name",
            type="line",
            value="",
            start=4,
            size=4,
            is_required=False,
        )
        Path(self.input_dir, "warnings.txt").write_text("GENBETA\n", encoding="utf-8")

        with patch.object(
            type(local),
            "_post_read_import_file",
            autospec=True,
            return_value={"generated": ["Partner A"], "not_generated": ["Partner B"]},
        ):
            result = local.read_import_file()

        self.assertEqual(result["params"]["type"], "warning")
        self.assertRegex(
            result["params"]["message"],
            "Some files were imported|Se importaron algunos archivos",
        )

    def test_header_code_must_be_unique(self):
        self.edi_local_header_model.create(
            {
                "code": "dup_test",
                "name": "Duplicate test",
            }
        )

        with self.assertRaisesRegex(ValidationError, "unique|único"):
            self.edi_local_header_model.create(
                {
                    "code": "dup_test",
                    "name": "Duplicate test 2",
                }
            )

    def test_line_overlap_validation(self):
        local = self._create_local()
        self._create_line(
            local,
            name="first_value",
            start=1,
            size=4,
            value="result = 'ABCD'",
        )

        with self.assertRaisesRegex(ValidationError, "overlap|solapan"):
            self._create_line(
                local,
                name="second_value",
                start=2,
                size=4,
                value="result = 'EFGH'",
            )

    def test_line_helper_methods(self):
        local = self._create_local()
        numeric_line = self._create_line(
            local,
            name="numeric_value",
            type_data="numeric",
            size=5,
            decimal=2,
            fill_value=True,
            value_fill="0",
            value="result = 12.3",
        )
        alphanumeric_line = self._create_line(
            local,
            name="alpha_value",
            type_data="alphanumeric",
            start=10,
            size=5,
            trunc_value=True,
            value="result = 'ABCDEFG'",
            check_override=False,
        )

        self.assertEqual(numeric_line.fill_value_by_size("12.3"), "012.30")
        self.assertEqual(alphanumeric_line._trunc_value("ABCDEFG"), "ABCDE")
        self.assertEqual(alphanumeric_line._get_translated_selection_label(), "Header")

    def test_utils_helpers(self):
        self.assertTrue(is_numeric("12", partial_integer=2))
        self.assertFalse(is_numeric("123", partial_integer=2))
        self.assertTrue(is_numeric("-12.34", partial_integer=3, partial_decimal=2))
        self.assertTrue(is_alphanumeric("ABC 123"))
        self.assertFalse(is_alphanumeric("ABC-123"))
        self.assertTrue(is_date("20250131"))
        self.assertFalse(is_date("20251331"))

        notification = get_notification("Done", type_message="success")

        self.assertEqual(notification["params"]["type"], "success")
        self.assertEqual(notification["params"]["message"], "Done")
