# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import inspect

from pytz import timezone

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from odoo.tools.safe_eval import safe_eval, test_python_expr

from ..utils import is_alphanumeric, is_date, is_numeric


class EdiLocalLine(models.Model):
    _name = "edi.local.line"
    _description = "Edi local line"

    edi_local_id = fields.Many2one("edi.local", ondelete="cascade")
    model_name = fields.Char(related="edi_local_id.model_name")
    model_id = fields.Many2one("ir.model", related="edi_local_id.model_id")
    sequence = fields.Integer()
    type = fields.Selection(
        [
            ("header", "Header"),
            ("line", "Lines"),
        ],
        default="header",
        help="",
    )
    type_header = fields.Many2one(
        "edi.local.header",
        help="Defines after which header the lines are generated, "
        "if not specified it is generated at the end of everything",
    )
    name = fields.Char(required=True)
    description = fields.Char(help="A description of the value the field accepts.")
    type_data = fields.Selection(
        [
            ("alphanumeric", "Alphanumeric"),
            ("numeric", "Numeric"),
            ("date", "Date"),
            ("general", "General"),
        ],
        default="alphanumeric",
        help="Defines the data type of the value\n"
        "Alphanumeric: Only letters and numbers are allowed. Example: Alpha12pha345\n"
        "Numeric: Only numbers are allowed. Example: 12345\n"
        "Date: Only dates are allowed. Example: 20251112\n"
        "General: Any value is allowed. Example: Alpha1_2pha345-*_",
    )
    start = fields.Integer(
        help="Defines the position from which counting will begin based on "
        "the size value. By default, this is the last position "
        "of the previous line in the same header.",
        store=True,
    )
    size = fields.Integer(
        help="Defines the field size. Example: 5 positions", required=True, default=1
    )
    end = fields.Integer(compute="_compute_end", store=True)
    decimal = fields.Integer(
        default=0,
        help="Defines the number of decimal places in the "
        "number. These decimal places are taken into "
        "account in the length (start + size)",
    )
    is_required = fields.Boolean(
        default=True,
    )
    fill_value = fields.Boolean(
        default=False,
        help="Defines whether the value size is filled with "
        "a specific character; if the default character "
        "is not defined, it is filled with a space.",
    )
    trunc_value = fields.Boolean(
        default=True,
        help="If this option is selected, it defines that if "
        "the value does not meet the defined size, "
        "then it will be cut to that size.",
    )
    value_fill = fields.Char(
        help="Defines the value to be filled, by default it is a space."
    )
    orientation_fill_value = fields.Selection(
        [("left", "Left"), ("center", "Center"), ("right", "Right")],
        default="right",
        help="Defines the orientation in which " "the filling will be carried out.",
    )
    value = fields.Text(default="")
    check_override = fields.Boolean(
        default=True,
        help="""Defines whether to validate overlapping positions (start + size).
                Example use: If two fields must use the same value when importing
                a file, then this field is defined as True to prevent an overlap
                error from being thrown during the process; this use case is
                typically during import.
                The default is true.
                """,
    )

    @api.depends("start", "size")
    def _compute_end(self):
        for line in self:
            line.end = line.start + line.size

    @api.constrains("start", "size")
    def _check_start(self):
        for line in self:
            if not line.check_override:
                continue
            overlap = self.search_read(
                [
                    ("type", "=", line.type),
                    ("type_header", "=", line.type_header.id),
                    ("start", "<", line.end),
                    ("model_name", "=", line.edi_local_id.model_name),
                    ("edi_local_id", "=", line.edi_local_id.id),
                    ("end", ">", line.start),
                    ("id", "!=", line.id),
                ],
                ["name", "start", "end"],
                limit=1,
            )
            if overlap:
                self.edi_local_id._message_error(
                    _(
                        "The start %(start)s and %(end)s values overlap with the "
                        "%(line_name)s line."
                        "\nOverlap: Start: %(start_overlap)s End: %(end_overlap)s"
                    )
                    % {
                        "start": line.start,
                        "end": line.end,
                        "line_name": overlap[0]["name"],
                        "start_overlap": overlap[0]["start"],
                        "end_overlap": overlap[0]["end"],
                    }
                )

    @api.onchange("value")
    def _onchange_value(self):
        for local in self:
            local._normalize_code()
            if local.value:
                local._test_python_expr()

    def _normalize_code(self):
        format_value = self.value or ""
        format_value = format_value.replace("\r\n", "\n")
        format_value = format_value.expandtabs(4)
        self.value = inspect.cleandoc(format_value).strip()

    def _not_check_value(self, record, value):
        return False

    def _get_translated_selection_label(self, field_name="type"):
        field_info = self.fields_get(allfields=[field_name]).get(field_name, {})
        return dict(field_info.get("selection", [])).get(self.type, self.type)

    def _show_message_error_line(self, record, value, message_error):
        context = dict(self.env.context)
        attachment_id = context.get("attachment_id", False)
        with_cron = context.get("generate_with_cron", False) or context.get(
            "import_with_cron", False
        )
        leap_line = "<br/>" if with_cron else "\n"
        self.edi_local_id._message_error(
            _(
                "%(error)s"
                "%(file)s "
                "%(leap_line)sType: %(type)s "
                "%(leap_line)sValue: %(value)s "
                "%(leap_line)sField: %(field_name)s "
                "%(leap_line)sExpression: %(expression)s "
                "%(leap_line)sRecord [%(model_name)s]: %(record_name)s "
                "%(leap_line)sError: %(message)s"
            )
            % {
                "error": _("An error occurred while generating the files:")
                if with_cron
                else "",
                "leap_line": leap_line,
                "file": _("%(leap_line)sFile: %(file_name)s")
                % {"file_name": attachment_id.name, "leap_line": leap_line}
                if attachment_id
                else "",
                "type": self._get_translated_selection_label(),
                "field_name": self.name,
                "model_name": self.model_id.name,
                "record_name": getattr(record, "name", ""),
                "value": value if value else _("No defined"),
                "expression": self.value,
                "message": message_error,
            },
            send_email=True,
        )

    def _valid_is_numeric(self, **values):
        value = values.get("value")
        partial_integer = self.size - self.decimal
        partial_decimal = self.decimal
        valid = True
        if not is_numeric(
            value=value,
            partial_integer=values.get("partial_integer", partial_integer),
            partial_decimal=values.get("partial_decimal", partial_decimal),
        ) or (values.get("is_digit", False) and not value.isdigit()):
            valid = False
            self._show_message_error_line(
                self,
                value,
                _(
                    "It is not a valid number with %(partial_integer)s "
                    "whole digits and %(partial_decimal)s decimal places."
                )
                % {
                    "partial_integer": partial_integer,
                    "partial_decimal": partial_decimal,
                },
            )
        return valid

    def _valid_is_alphanumeric(self, **values):
        value = values.get("value")
        valid = True
        if not is_alphanumeric(
            value=value,
            allow_character=" "
            if self.fill_value and not self.value_fill
            else self.value_fill,
        ):
            valid = False
            self._show_message_error_line(
                self,
                value,
                _(
                    "This is not a valid value for an alphanumeric character. "
                    "Example: CAB159ED"
                ),
            )
        return valid

    def _valid_is_date(self, **values):
        value = values.get("value")
        valid = True
        if not is_date(value=value):
            valid = False
            self._show_message_error_line(
                self,
                value,
                _(
                    "This is not a valid value for a date in YYYYMMDD format. "
                    "Example: 20250902"
                ),
            )
        return valid

    def _check_value(self, record, value):
        check_valid = True
        if not self.is_required and not value:
            return check_valid
        value_size = (
            self.size + 1
            if self.type_data == "numeric" and self.decimal > 0
            else self.size
        )
        if isinstance(value, (int | float)):
            value = str(value)
        if len(value) > value_size:
            self._show_message_error_line(
                record,
                value,
                _("The value is longer than the allowed size (%(size)s). ")
                % {
                    "size": value_size,
                },
            )
            check_valid = False
        elif self.is_required and (not value or value is None):
            self.edi_local_id._message_error(
                _("[%(header)s] The field %(field)s (%(description)s) is required")
                % {
                    "header": self.type_header.code,
                    "field": self.name,
                    "description": self.description,
                }
            )
            check_valid = False
        elif self.type_data == "numeric":
            check_valid = self._valid_is_numeric(**{"value": value})
        elif self.type_data == "alphanumeric":
            check_valid = self._valid_is_alphanumeric(**{"value": value})
        elif self.type_data == "date":
            check_valid = self._valid_is_date(**{"value": value})
        return check_valid

    def check_value(self, record, value):
        if self._not_check_value(record, value):
            return True
        return self._check_value(record, value)

    def _get_eval_context(self, eval_context=None):
        return {
            # orm
            "env": self.env,
            "model": self.env[self.model_name],
            # record
            "record": None,
            "_": _,
            # exceptions
            "UserError": UserError,
            # tools
            "time": tools.safe_eval.time,
            "datetime": tools.safe_eval.datetime,
            "dateutil": tools.safe_eval.dateutil,
            "timezone": timezone,
            "float_compare": float_compare,
            "result": False,
        } | (eval_context or {})

    def _test_python_expr(self):
        # Evaluating expression syntax
        if self.value:
            msg = test_python_expr(expr=self.value, mode="exec")
            if msg:
                self.edi_local_id._message_error(msg)
        return True

    def _trunc_value(self, value):
        if self.trunc_value:
            trunc_size = self.size
            if self.type_data == "numeric" and self.decimal > 0 and "." in value:
                trunc_size = self.size + 1
            return value[0:trunc_size]
        return value

    def _fill_value_numeric(self, **values):
        eval_value = values.get("eval_value", None)
        size = values.get("size", None)
        number_str = str(eval_value)
        if "." in number_str:
            integer, decimal = number_str.split(".", 1)
        else:
            integer, decimal = number_str, ""
        partial_integer = integer.zfill(size)
        if self.decimal:
            partial_decimal = decimal.ljust(self.decimal, "0")[: self.decimal]
            value_complete = f"{partial_integer}.{partial_decimal}"
        else:
            value_complete = partial_integer
        return value_complete

    def _fill_value_alphanumeric(self, **values):
        eval_value = values.get("eval_value", None)
        size = values.get("size", None)
        if self.orientation_fill_value == "left":
            value_complete = (
                str(eval_value).rjust(size, str(self.value_fill))
                if self.value_fill
                else str(eval_value).rjust(size)
            )
        elif self.orientation_fill_value == "center":
            value_complete = (
                str(eval_value).center(size, str(self.value_fill))
                if self.value_fill
                else str(eval_value).center(size)
            )
        else:
            value_complete = (
                str(eval_value).ljust(size, str(self.value_fill))
                if self.value_fill
                else str(eval_value).ljust(size)
            )
        return value_complete

    def _fill_value_date(self, **values):
        eval_value = values.get("eval_value", None)
        size = values.get("size", None)
        if self.value_fill:
            value_complete = str(eval_value).rjust(size, str(self.value_fill))
        else:
            value_complete = str(eval_value).rjust(size)
        return value_complete

    def fill_value_by_size(self, eval_value):
        size = self.size - self.decimal
        if self.type_data in ("general", "alphanumeric"):
            value_complete = self._fill_value_alphanumeric(
                **{"eval_value": eval_value, "size": size}
            )
        elif self.type_data == "numeric":
            value_complete = self._fill_value_numeric(
                **{"eval_value": eval_value, "size": size}
            )
        elif self.type_data == "date":
            value_complete = self._fill_value_date(
                **{"eval_value": eval_value, "size": size}
            )
        else:
            value_complete = eval_value
        return value_complete

    def _eval_value(self, record, global_context_by_record):
        self._normalize_code()
        self._test_python_expr()
        global_context_by_record.update(
            {
                "record": record,
            }
        )
        if not self.value:
            return (
                (self.fill_value_by_size(" ") if self.fill_value else "")
                if self.edi_local_id.type == "out"
                else {self.name: record}
            )
        context = self._get_eval_context(eval_context=global_context_by_record)
        try:
            safe_eval(
                self.value,
                mode="exec",
                nocopy=True,
                globals_dict=context,
            )
        except Exception as ex:
            return self._show_message_error_line(record, None, str(ex))
        if context.get("result", False) is False and self.value:
            self._show_message_error_line(
                record,
                None,
                _("Please define the variable `result` with the final result."),
            )
            return False
        value = context.get("result", False)
        if self.edi_local_id.type == "out":
            result = self._trunc_value(str(value))
            has_invalid_decimals = (
                self.type_data == "numeric"
                and self.decimal > 0
                and (
                    "." not in str(result)
                    or len(str(result).split(".", 1)[1]) != self.decimal
                )
            )
            if self.fill_value and (
                len(str(result)) < self.size or has_invalid_decimals
            ):
                result = self.fill_value_by_size(result)
            result_check = self.check_value(record, result)
            if not result_check:
                return False
        else:
            result = {self.name: value}
        return result

    def _eval_line(self, record, global_context_by_record):
        context = dict(self.env.context)
        eval_value = self.with_context(**context)._eval_value(
            record, global_context_by_record
        )
        return eval_value

    def _parse_value(self, value):
        self.ensure_one()
        parse_value = value[self.start - 1 : self.end - 1]
        parse_value = parse_value.replace(self.value_fill or " ", "")
        if self.type_data == "numeric" and parse_value:
            self._valid_is_numeric(**{"value": parse_value, "is_digit": True})
            parse_entire = parse_value[0 : self.size]
            partial_decimal = False
            if self.decimal:
                partial_decimal = parse_value[self.size : self.size + self.decimal :]
            parse_value = float(
                f"{parse_entire}.{partial_decimal or 0}"
                if self.decimal
                else parse_entire
            )
        elif self.type_data == "alphanumeric" and parse_value:
            self._valid_is_alphanumeric(**{"value": parse_value})
        elif self.type_data == "date" and parse_value:
            self._valid_is_date(**{"value": parse_value})
        return parse_value
