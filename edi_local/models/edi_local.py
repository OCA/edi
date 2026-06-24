# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io
import mimetypes
import os
import textwrap
from pathlib import Path

from markupsafe import Markup, escape

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

from ..utils import get_notification


class EdiLocal(models.Model):
    _name = "edi.local"
    _inherit = ["mail.thread", "mail.activity.mixin", "edi.local.mixin"]
    _description = "Edi Local"

    sequence_id = fields.Many2one("ir.sequence", string="Filename")
    name = fields.Char(required=True, tracking=True)
    model_id = fields.Many2one(
        "ir.model", required=True, ondelete="cascade", tracking=True
    )
    model_name = fields.Char(
        related="model_id.model",
        string="Model Name",
        readonly=True,
        inverse="_inverse_model_name",
    )
    field_id = fields.Many2one(
        "ir.model.fields",
        domain="[('model', '=', model_name), "
        "('ttype', 'in', ('one2many', 'many2many'))]",
    )
    after_header = fields.Many2one(
        "edi.local.header",
        help="Defines after which header the lines are generated, "
        "if not specified it is generated at the end of everything",
    )
    local_line_ids = fields.One2many(
        "edi.local.line", "edi_local_id", copy=True, domain=[("type", "=", "header")]
    )
    line_ids = fields.One2many(
        "edi.local.line", "edi_local_id", copy=True, domain=[("type", "=", "line")]
    )
    description = fields.Char()
    domain = fields.Char(string="Apply on", tracking=True)
    enabled = fields.Boolean(default=False)
    files_generated = fields.Text()
    file_type = fields.Selection([("txt", "Text")], required=True, default="txt")
    override_file = fields.Boolean(
        default=True,
        tracking=True,
        help="Defines whether existing files are deleted when regenerating.",
    )
    dir_file = fields.Char(
        tracking=True,
        help="Defines the local directory where the generated files will be stored.",
    )
    dir_import_file = fields.Char(
        tracking=True,
        help="""
            Define the local directory from which the files to be imported will be read.
            These will be added to the attachments if they already exist.
        """,
    )
    has_configuration_error = fields.Boolean(
        default=False,
        help="Determine if there was an error in the generation or import of files.",
    )
    type = fields.Selection(
        [("in", "In"), ("out", "Out")], required=True, default="out"
    )
    attachment_ids = fields.Many2many("ir.attachment")
    available_variables = fields.Text(compute="_compute_available_variables")

    def _get_available_variables_text(self):
        return _(
            "# Available variables:\n"
            "#  - env: environment on which the action is triggered\n"
            "#  - record:\n"
            "#        When the type is 'out': it's the record on which the action is "
            "triggered.\n"
            "#        When the type is 'in': it's the value of the element retrieved "
            "from the\n"
            "#                                    file, usually a string.\n"
            "#  - model: model of the record on which the action is triggered; is a "
            "void recordset\n"
            "#  - time, datetime, dateutil, timezone: useful Python libraries\n"
            "#  - float_compare: utility function to compare floats based on "
            "specific precision\n"
            "#  - UserError: exception class for raising user-facing warning messages\n"
            "#  - result: Variable in which the final result is stored\n"
        )

    def _compute_available_variables(self):
        available_variables = self._get_available_variables_text()
        for local in self:
            local.available_variables = available_variables

    @api.constrains("dir_file", "dir_import_file")
    def _check_directories(self):
        for rec in self:
            rec.valid_dir_file()

    def _inverse_model_name(self):
        for rec in self:
            rec.model_id = self.env["ir.model"]._get(rec.model_name)

    # ==========================================================
    # GENERAL
    # ==========================================================

    def get_eval_domain(self):
        return self.env[self.model_name].search(safe_eval(self.domain))

    def _message_error(self, message_error, send_email=False):
        self.has_configuration_error = True
        if isinstance(message_error, Exception):
            if len(message_error.args) == 1:
                message_error = message_error.args[0]
            else:
                message_error = str(message_error)

        if message_error in (False, None):
            return

        if isinstance(message_error, str):
            message_error = message_error.strip()
            if message_error.lower() in ("false", "none", ""):
                return

        context = dict(self.env.context)
        with_cron = context.get("generate_with_cron", False) or context.get(
            "import_with_cron", False
        )

        if with_cron and send_email:
            self.notification_message_edi(
                edi_local_id=self,
                message_text=Markup(message_error),
                message_values={},
            )
        elif with_cron and not send_email:
            self.message_post(body=message_error, body_is_html=True)
        else:
            raise ValidationError(message_error)

    def _global_context_by_record(self, record=None):
        """
        This method passes a dictionary as a context when
        evaluating each of the record's values (values that match the domain).
        For example:
            The value of the Apply on field matches four records,
            so these values are evaluated for each record, not for
            each Header or Line.
        """
        return {}

    def _context_by_line(self, record_line):
        return {}

    def _get_values_grouped(self, headers=False, all_lines=False):
        if all_lines:
            values = self.local_line_ids | self.line_ids
        else:
            values = self.line_ids if not headers else self.local_line_ids
        return values.sorted(
            lambda local_line: local_line.type_header.sequence
        ).grouped("type_header")

    # ==========================================================
    # GENERATE FILE
    # ==========================================================

    def _valid_write_dir(self, dir_valid):
        try:
            os.makedirs(dir_valid, exist_ok=True)
            path = os.path.join(dir_valid, ".perm_test.tmp")
            with open(path, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(path)
        except OSError:
            self._message_error(
                _("The defined directory (%(dir_valid)s) is not accessible.")
                % {
                    "dir_valid": dir_valid,
                },
                send_email=True,
            )
            return False

    def _valid_read_dir(self, dir_valid):
        if not os.path.isdir(dir_valid):
            self._message_error(
                _("The defined directory (%(dir_valid)s) does not exist.")
                % {
                    "dir_valid": dir_valid,
                },
                send_email=True,
            )
            return False
        if not os.access(dir_valid, os.R_OK | os.X_OK):
            self._message_error(
                _("The defined directory (%(dir_valid)s) cannot be accessible.")
                % {
                    "dir_valid": dir_valid,
                },
                send_email=True,
            )
            return False
        return True

    def valid_dir_file(self):
        self.ensure_one()
        if self.dir_file and self.type == "out":
            return self._valid_write_dir(self.dir_file)
        elif self.dir_import_file and self.type == "in":
            return self._valid_read_dir(self.dir_import_file)
        return True

    def remove_files(self):
        for file in self.files_generated.split(","):
            file_path = Path(file)
            if file_path.exists():
                file_path.unlink()

    def save_file(self, files):
        files_generated = []
        if self.valid_dir_file() is not True:
            return False
        try:
            for file in files:
                filename, value_file = next(iter(file.items()))
                path = os.path.join(self.dir_file, f"{filename}.txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(value_file)
                files_generated.append(path)
        except FileNotFoundError as ex:
            self._message_error(str(ex), send_email=True)
        except Exception as ex:
            self._message_error(ex, send_email=True)
        return files_generated

    def get_filename(self):
        return self.sequence_id.next_by_id()

    def _skip_value_lines(self, line):
        """
        This method allows you to ignore records based on certain conditions.
        Example:
        If the quantity of a sales line is 0, then that line should not be generated
        in the final file.

        :param line: Current record
        :return: bool
        """
        return False

    def _eval_lines(self, record, global_context_by_record):
        """
        This method generates the lines according to the configuration of the Lines tab.
        """
        eval_value = ""
        line_grouped = self._get_values_grouped()
        for _unused, values in line_grouped.items():
            for num_line, line in enumerate(
                getattr(record, self.field_id.name, []), start=1
            ):
                context_by_line = (global_context_by_record or {}).copy()
                context_by_line.update(self._context_by_line(line))
                context_by_line.update({"num_line": num_line})
                if self._skip_value_lines(line):
                    continue
                for value in values:
                    eval_line = value._eval_line(line, context_by_line)
                    if eval_line is False or eval_line is None:
                        return False
                    else:
                        eval_value += eval_line
                eval_value += "\n"
        return eval_value

    def _eval_headers_lines(self, record=None):
        """
        This method generates the lines according
        to the configuration of the Headers tab.
        """
        local_line_grouped = self._get_values_grouped(headers=True)
        global_context_by_record = self._global_context_by_record(record)
        eval_value = ""
        for type_header, values in local_line_grouped.items():
            for value in values:
                eval_line = value._eval_line(record, global_context_by_record)
                if eval_line is False or eval_line is None:
                    return False
                else:
                    if isinstance(eval_line, dict):
                        global_context_by_record.update(eval_line)
                    eval_value += eval_line

            if self.after_header and self.after_header == type_header and self.field_id:
                eval_value += "\n"
                eval_value_line = self._eval_lines(record, global_context_by_record)
                if eval_value_line is False or eval_value_line is None:
                    return False
                else:
                    eval_value += eval_value_line
            eval_value += "\n"
        return eval_value

    def _post_generate_file(self, record):
        """
        params:
            record: record that matches the configured domain

        This method is executed after generating a file for
        one of the records that matches the configured domain.
        For example:
        When generating a file for an invoice, a 'Generated file'
        field is set to allow the user to filter.
        """
        pass

    def post_generate_file(self, record):
        context = dict(self.env.context)
        if not context.get("test_generate_file", False):
            self._post_generate_file(record)

    def generate_file_txt(self, records):
        files = []
        for record in records:
            filename = self.get_filename()
            eval_value = self._eval_headers_lines(record)
            if eval_value:
                files.append({filename: textwrap.dedent(eval_value).lstrip("\n")})
                self.post_generate_file(record)
        return files

    def valid_generate_file(self):
        self.ensure_one()
        if not self.sequence_id:
            self._message_error(_("Define a filename"))

    def generate_file(self):
        context = dict(self.env.context)
        generate_with_cron = context.get("generate_with_cron", False)
        for local in self:
            if local.enabled or context.get("test_generate_file", False):
                local.has_configuration_error = False
                local.valid_before_read_or_generate_file()
                local.valid_generate_file()
                func_name = f"generate_file_{local.file_type}"
                func_export_type = getattr(local, func_name, None)
                if func_export_type:
                    try:
                        records = local.get_eval_domain()
                        if records:
                            result_files = func_export_type(records)
                            if (
                                result_files
                                and not context.get("test_generate_file", False)
                                and not local.has_configuration_error
                            ):
                                files_generated = local.save_file(result_files)
                                if files_generated:
                                    if local.override_file:
                                        if local.files_generated:
                                            local.remove_files()
                                        local.files_generated = ",".join(
                                            files_generated
                                        )
                                    else:
                                        local.files_generated += "," + ",".join(
                                            files_generated
                                        )
                                    message_text = Markup("%s<br/>%s") % (
                                        escape(
                                            _("The following files were generated:")
                                        ),
                                        Markup("<br/>").join(
                                            escape(file_name)
                                            for file_name in files_generated
                                        ),
                                    )
                                    local.message_post(
                                        body=message_text,
                                    )
                                    if not generate_with_cron:
                                        return get_notification(
                                            _("All files were generated successfully."),
                                            type_message="success",
                                        )
                                else:
                                    if not generate_with_cron:
                                        return get_notification(
                                            _(
                                                """
                                            The files were not generated.
                                            For more details, please review the notes.
                                            """
                                            ),
                                            type_message="warning",
                                        )
                        else:
                            local._message_error(
                                _(
                                    "There are no records with "
                                    "the conditions defined in the Apply on field."
                                )
                            )
                    except Exception as ex:
                        local._message_error(ex)
                else:
                    local._message_error(
                        _(
                            "I do not generate documents of type %(document_type)s "
                            "because the function with structure "
                            " %(func_structure)s does not exist."
                        )
                        % {
                            "document_type": local.file_type,
                            "func_structure": func_name,
                        }
                    )

    # ==========================================================
    # READ IMPORT FILE
    # ==========================================================

    @api.constrains("attachment_ids", "file_type")
    def _check_file(self):
        for local in self:
            for att in local.attachment_ids:
                name = (att.name or "").lower()
                ext = os.path.splitext(name)[1]
                if ext != f".{local.file_type.lower()}":
                    local._message_error(
                        _(
                            "The document (%(document_name)s) extension is "
                            "not the allowed one .%(file_type)s."
                        )
                        % {
                            "document_name": att.name,
                            "file_type": local.file_type,
                        }
                    )

    def _post_read_import_file(self, value_list):
        return {}

    def post_read_import_file(self, value_list):
        """
        Read the attached document(s) and evaluate each line of the configuration.
        :param value_list: dict
        :return: list of dict
        """
        context = dict(self.env.context)
        if value_list:
            generateds = self._post_read_import_file(value_list) or None
            if not context.get("test_read_import_file", False) and generateds:
                model_name = self.model_name.replace(".", " ").capitalize()
                message_text = Markup("")
                generated = generateds.get("generated", [])
                not_generated = generateds.get("not_generated", [])
                if generated:
                    message_text += Markup(
                        _("The %(model_name)s were generated: %(generated)s<br/><br/>")
                    ) % {
                        "model_name": escape(model_name),
                        "generated": Markup("<br/>%s")
                        % Markup("<br/>").join(
                            item if isinstance(item, Markup) else escape(item)
                            for item in generated
                        ),
                    }
                if not_generated:
                    message_text += Markup(
                        _("The %(model_name)s not were generated: %(not_generated)s")
                    ) % {
                        "model_name": escape(model_name),
                        "not_generated": Markup("<br/>%s")
                        % Markup("<br/>").join(
                            item if isinstance(item, Markup) else escape(item)
                            for item in not_generated
                        ),
                    }
                    if message_text:
                        self.notification_message_edi(
                            edi_local_id=self,
                            message_text=message_text,
                            message_values={},
                        )
                if not context.get("import_with_cron", False):
                    if generated and not not_generated:
                        return get_notification(
                            _("All files were imported successfully."),
                            type_message="success",
                        )
                    elif not generated and not_generated:
                        return get_notification(
                            _(
                                """
                                The files were not imported.
                                For more details, please see the notes.
                                """
                            ),
                            type_message="warning",
                        )
                    elif generated and not_generated:
                        return get_notification(
                            _(
                                """
                                Some files were imported.
                                For more details, see the notes.
                                """
                            ),
                            type_message="warning",
                        )
        return {}

    def valid_read_file(self):
        pass

    def read_file_txt(self, **values):
        if values.get("bs4_data", False):
            file_import_raw = base64.b64decode(values["bs4_data"])
            file_text = io.TextIOWrapper(
                io.BytesIO(file_import_raw),
                encoding=values.get("encoding", "utf-8"),
                errors="replace",
            )
            return file_text.readlines()
        return []

    def read_files_by_directory(self):
        self.ensure_one()
        IrAttachment = self.env["ir.attachment"].sudo()
        attachment_ids = []
        attachments = []
        context = dict(self.env.context)
        if self.dir_import_file and self.type == "in":
            if self.attachment_ids:
                self.attachment_ids.sudo().unlink()
            file_extension = f".{(self.file_type or '').lower().lstrip('.')}"
            for filename in os.listdir(self.dir_import_file):
                file_path = os.path.join(self.dir_import_file, filename)
                if not os.path.isfile(file_path):
                    continue
                if file_extension and not filename.lower().endswith(file_extension):
                    continue

                with open(file_path, "rb") as f:
                    file_content = f.read()

                mimetype = (
                    mimetypes.guess_type(file_path)[0] or "application/octet-stream"
                )

                attachment = IrAttachment.create(
                    {
                        "name": filename,
                        "type": "binary",
                        "datas": base64.b64encode(file_content).decode("utf-8"),
                        "mimetype": mimetype,
                        "res_model": self._name,
                        "res_id": self.id,
                    }
                )
                attachments.append(filename)

                attachment_ids.append(attachment.id)
            if attachment_ids:
                self.attachment_ids = [Command.set(attachment_ids)]
                self.message_post(
                    body=_(
                        "The following files were retrieved from "
                        "directory %(directory)s: %(attachments)s"
                    )
                    % {
                        "attachments": f"<br/><br/> {', '.join(attachments)}",
                        "directory": self.dir_import_file,
                    },
                    body_is_html=True,
                )
            elif not context.get("import_with_cron", False):
                self._message_error(
                    _("No files to read were detected in the directory %(directory)s.")
                    % {
                        "directory": self.dir_import_file,
                    }
                )

    def read_import_file_txt(self):
        self.ensure_one()
        lines = self._get_values_grouped(all_lines=True)
        value_list = []
        for attachment in self.attachment_ids:
            try:
                global_context_by_record = self._global_context_by_record()
                lines_import = self.read_file_txt(**{"bs4_data": attachment.datas})
                field_name = self.field_id.name
                value_dict = {}
                values_line = []
                attachment_failed = False
                for index in range(len(lines_import)):
                    line = lines_import[index].rstrip("\n")
                    value_line = {}
                    for type_header, values in lines.items():
                        if not line.lstrip().startswith(type_header.code.upper()):
                            continue
                        if not value_dict.get(type_header.code, False):
                            value_dict[type_header.code] = {}
                        for value in values:
                            record_value = value._parse_value(line)
                            eval_line = value.with_context(
                                attachment_id=attachment
                            )._eval_line(record_value, global_context_by_record)
                            if not isinstance(eval_line, dict):
                                attachment_failed = True
                                break
                            global_context_by_record.update(eval_line)
                            if value.type == "line":
                                value_line.update(eval_line)
                            else:
                                value_dict[type_header.code].update(eval_line)
                        if attachment_failed:
                            break
                    if attachment_failed:
                        break
                    if value_line:
                        values_line.append(Command.create(value_line))
                if attachment_failed:
                    continue
                if values_line:
                    value_dict[field_name] = values_line
                value_list.append(value_dict)
            except Exception as ex:
                self._message_error(ex, send_email=True)
                continue
        return value_list

    def read_import_file(self):
        context = dict(self.env.context)
        value_list = []
        for local in self:
            if local.dir_import_file:
                valid_directory_import = local._valid_read_dir(local.dir_import_file)
                if valid_directory_import is not True:
                    continue
                local.read_files_by_directory()
            if (
                local.type == "in"
                and not local.attachment_ids
                and not context.get("import_with_cron", False)
            ):
                local._message_error(
                    _(
                        "No file was detected. You must upload a "
                        "file to proceed with the import."
                    )
                )
            if local.enabled or context.get("test_read_import_file", False):
                local.valid_before_read_or_generate_file()
                local.valid_read_file()
                func_name = f"read_import_file_{local.file_type}"
                func_import_type = getattr(local, func_name, None)
                if func_import_type:
                    try:
                        value_list = func_import_type()
                    except Exception as ex:
                        local._message_error(ex)
                else:
                    local._message_error(
                        _(
                            "Documents of type %(document_type)s "
                            "were not imported "
                            "because the function with structure "
                            " %(func_structure)s does not exist."
                        )
                        % {
                            "document_type": local.file_type,
                            "func_structure": func_name,
                        }
                    )
            return local.post_read_import_file(value_list)

    def valid_before_read_or_generate_file(self):
        self.ensure_one()
        if not self.local_line_ids:
            self._message_error(
                _("Define lines before generating a file"), send_email=True
            )

    @api.model
    def get_domain_cron(self, type_edi="out"):
        return [
            ("enabled", "=", True),
            ("type", "=", type_edi),
            "|",
            ("local_line_ids", "!=", False),
            ("line_ids", "!=", False),
        ]

    @api.model
    def generate_file_cron(self):
        cron_context = dict(self.env.context)
        cron_context.setdefault("lang", self.env.user.lang)
        cron_context.setdefault("generate_with_cron", True)
        cron_self = self.with_context(**cron_context)
        for local in cron_self.search(cron_self.get_domain_cron()):
            if local.get_eval_domain():
                local.generate_file()

    @api.model
    def import_file_cron(self):
        cron_context = dict(self.env.context)
        cron_context.setdefault("lang", self.env.user.lang)
        cron_context.setdefault("import_with_cron", True)
        cron_self = self.with_context(**cron_context)
        for local in cron_self.search(cron_self.get_domain_cron("in")):
            local.read_import_file()
