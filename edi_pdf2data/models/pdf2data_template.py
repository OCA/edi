# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import os
import re
import shutil
import subprocess
from collections import OrderedDict
from tempfile import NamedTemporaryFile

import dateparser
import yaml
from unidecode import unidecode

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Pdf2dataTemplate(models.Model):
    _name = "pdf2data.template"
    _description = "Pdf2data Template"
    _order = "sequence"

    name = fields.Char()
    code = fields.Char(related="type_id.code")
    type_id = fields.Many2one("pdf2data.template.type")
    exchange_type_id = fields.Many2one("edi.exchange.type", required=True)
    pdf2data_template_dict = fields.Serialized()
    pdf2data_options_dict = fields.Serialized()
    pdf_file = fields.Binary(attachment=True)
    pdf_filename = fields.Char()
    file_result = fields.Char(readonly=True)
    sequence = fields.Integer(default=20)
    extracted_text = fields.Text(readonly=True)
    field_ids = fields.One2many("pdf2data.template.field", inverse_name="template_id")
    lang = fields.Selection(string="Language", selection="_get_lang")
    decimal_separator = fields.Char(default=".")
    remove_whitespace = fields.Boolean()
    remove_accents = fields.Boolean()
    lowercase = fields.Boolean()
    keyword_ids = fields.One2many(
        "pdf2data.template.keyword",
        inverse_name="template_id",
        domain=[("exclude", "=", False)],
    )
    exclude_keyword_ids = fields.One2many(
        "pdf2data.template.keyword",
        inverse_name="template_id",
        domain=[("exclude", "=", True)],
    )
    replace_ids = fields.One2many(
        "pdf2data.template.replace", inverse_name="template_id",
    )

    @api.model
    def _get_lang(self):
        return self.env["res.lang"].get_installed()

    def _extract_pdf(self, data):
        data_file = NamedTemporaryFile(
            delete=False, prefix="odoo-simple-pdf-", suffix=".pdf"
        )
        try:
            data_file.write(base64.b64decode(data))
            data_file.close()
            if shutil.which("pdftotext"):
                extracted_str, err = subprocess.Popen(
                    ["pdftotext", "-layout", "-enc", "UTF-8", data_file.name, "-"],
                    stdout=subprocess.PIPE,
                ).communicate()
                extracted_str = extracted_str.decode("utf-8")
            else:
                raise EnvironmentError(
                    "pdftotext not installed. Can be downloaded "
                    "from https://poppler.freedesktop.org/"
                )
        finally:
            os.unlink(data_file.name)
        return extracted_str

    def _parse_pdf(self, data):
        extracted_str = self._extract_pdf(data)
        for template in self:
            optimized_str = template._prepare_input(extracted_str)
            if template._matches_input(optimized_str):
                return optimized_str, template._extract_data(optimized_str), template
        return False, False, False

    def _prepare_input(self, extracted_str):
        """
        Input raw string and do transformations, as set in template file.
        """

        # Remove withspace
        if self.remove_whitespace:
            optimized_str = re.sub(" +", "", extracted_str)
        else:
            optimized_str = extracted_str

        # Remove accents
        if self.remove_accents:
            optimized_str = unidecode(optimized_str)

        # convert to lower case
        if self.lowercase:
            optimized_str = optimized_str.lower()

        # specific replace
        for replace in self.replace_ids:
            optimized_str = re.sub(replace.from_char, replace.to_char, optimized_str)

        return optimized_str

    def _matches_input(self, optimized_str):
        """See if string matches all keyword patterns and no exclude_keyword
        patterns set in template file.
        Args:
        optimized_str: String of the text from OCR of the pdf after applying
        options defined in the template.
        Return:
        Boolean
            - True if all keywords are found and none of the exclude_keywords
                are found.
            - False if either not all keywords are found or at least one
                exclude_keyword is found."""
        if all(
            [re.search(keyword.keyword, optimized_str) for keyword in self.keyword_ids]
        ):
            # All keyword patterns matched
            exclude_keywords = self.exclude_keyword_ids
            if exclude_keywords:
                if any(
                    [
                        re.search(exclude_keyword.keyword, optimized_str)
                        for exclude_keyword in exclude_keywords
                    ]
                ):
                    # At least one exclude_keyword matches
                    _logger.debug(
                        "Template: %s. Keywords matched. Exclude keyword found!",
                        self.name,
                    )
                    return False
            # No exclude_keywords or none match, template is good
            _logger.debug(
                "Template: %s. Keywords matched. No exclude keywords found.", self.name
            )
            return True
        else:
            _logger.debug("Template: %s. Failed to match all keywords.", self.name)
            return False

    def _extract_data(self, optimized_str):
        """
        Given a template file and a string, extract matching data fields.
        """
        output = {}

        for field in self.field_ids:
            output[field.name] = field._extract_data(optimized_str, self)

        # required_fields = self.pdf2data_options_dict["required_fields"]
        required_fields = self.exchange_type_id.advanced_settings.get(
            "required_fields", []
        )

        if set(required_fields).issubset(output.keys()):
            return output
        else:
            fields = list(set(output.keys()))
            _logger.error(
                "Unable to match all required fields. "
                "The required fields are: {}. "
                "Output contains the following fields: {}.".format(
                    required_fields, fields
                )
            )
            return None

    def check_pdf(self):
        self.ensure_one()
        extracted_text, data, template = self._parse_pdf(self.pdf_file)
        if not template:
            self.write(
                {
                    "file_result": "Data cannot be processed",
                    "extracted_text": "No text extracted",
                }
            )
            return
        self.extracted_text = extracted_text
        self.file_result = yaml.dump(data)

    def _import_yml(self, data):
        lang = self.env.user.lang
        if data.get("options", {}).get("language"):
            lang = self.env["res.lang"]._lang_get_code(
                data.get("options", {}).get("language")
            )
        vals = {
            "keyword_ids": [(5, 0, 0)],
            "exclude_keyword_ids": [(5, 0, 0)],
            "field_ids": [(5, 0, 0)],
            "lang": lang,
        }
        for field in [
            "decimal_separator",
            "remove_whitespace",
            "remove_accents",
            "lowercase",
        ]:
            if data.get("options", {}).get(field):
                vals[field] = data.get("options", {})[field]
        keywords = data.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = [keywords]
        for keyword in keywords:
            vals["keyword_ids"].append((0, 0, {"keyword": keyword}))
        exclude_keywords = data.get("exclude_keywords", [])
        if not isinstance(exclude_keywords, list):
            exclude_keywords = [exclude_keywords]
        for keyword in exclude_keywords:
            vals["exclude_keyword_ids"].append(
                (0, 0, {"keyword": keyword, "exclude": True})
            )
        for field_name, field_data in data.get("fields", {}).items():
            vals["field_ids"].append(
                (0, 0, self._import_yml_field(field_name, field_data, data))
            )
        if vals:
            self.write(vals)

    def _import_yml_field(self, field_name, field_data, data):
        if isinstance(field_data, str):
            if field_name.startswith("static_"):
                return {
                    "name": field_name[7:],
                    "parse_mode": "static",
                    "value": field_data,
                    "kind": "str",
                }
            else:
                vals = {
                    "name": field_name,
                    "parse_mode": "regex",
                    "value": field_data,
                }
                if field_name.startswith("date"):
                    date_format = data.get("options", {}).get("date_formats", False)
                    if isinstance(date_format, list):
                        date_format = date_format[0]
                    vals.update({"kind": "date", "date_format": date_format})
                elif field_name.startswith("amount"):
                    vals["kind"] = "float"
                return vals
        vals = {"name": field_name, "parse_mode": field_data.get("parser", "regex")}
        if vals["parse_mode"] == "regex":
            vals.update(
                {
                    "kind": field_data.get("type", "str"),
                    "value": field_data.get("regex"),
                }
            )
            if vals["kind"] == "date":
                date_format = data.get("options", {}).get("date_formats", False)
                if isinstance(date_format, list):
                    date_format = date_format[0]
                vals["date_format"] = date_format
        elif vals["parse_mode"] == "static":
            vals.update({"kind": "str", "value": field_data.get("value")})
        return vals


class Pdf2dataTemplateField(models.Model):
    _name = "pdf2data.template.field"

    template_id = fields.Many2one("pdf2data.template", ondelete="cascade")
    field_id = fields.Many2one("pdf2data.template.field", ondelete="cascade")
    parse_mode = fields.Selection(
        [("regex", "Regex"), ("static", "Static"), ("line", "Line")],
        required=True,
        default="regex",
    )
    kind = fields.Selection(
        [("str", "String"), ("int", "Integer"), ("float", "Float"), ("date", "Date")]
    )
    name = fields.Char(required=True)
    value = fields.Text()
    date_format = fields.Char()
    decimal_separator = fields.Char()
    split_separator = fields.Char()
    line_separator = fields.Char()
    start_block = fields.Char()
    end_block = fields.Char()
    start = fields.Char()
    end = fields.Char()
    field_ids = fields.One2many("pdf2data.template.field", inverse_name="field_id")

    def _extract_data(self, optimized_str, template):
        return getattr(self, "_extract_data_%s" % self.parse_mode)(
            optimized_str, template
        )

    def _extract_data_static(self, content, template):
        return getattr(self, "_convert_type_%s" % (self.kind or "str"))(
            self.value, template
        )

    def _extract_data_line(self, content, template):
        start = re.search(self.start_block, content)
        end = re.search(self.end_block, content)
        if not start or not end:
            _logger.warning(f"No lines found. Start match: {start}. End match: {end}")
            return
        block_content = content[start.end() : end.start()]
        lines = []
        line_content = []
        for line in re.split(self.line_separator or "\n", block_content):
            if not line.strip("").strip("\n").strip("\r") or not line:
                continue
            if not line_content and re.search(self.start, line):
                line_content.append(line)
                continue
            if not line_content:
                continue
            line_content.append(line)
            if re.search(self.end, line):
                complied_content = (self.line_separator or "\n").join(line_content)
                lines.append(
                    {
                        field.name: field._extract_data(complied_content, template)
                        for field in self.field_ids
                    }
                )
                line_content = []
        return lines

    def _extract_data_regex(self, content, template):
        if not self.value:
            _logger.warning('Field "%s" doesn\'t have regex specified', self.name)
            return None

        regexes = self.value.split("\n")
        result = []
        for regex in regexes:
            matches = re.findall(regex, content)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        _logger.warning(
                            "Regex can't contain multiple capturing groups (\""
                            + regex
                            + '")'
                        )
                        return None
                result += matches
        settings_type = self.kind or "str"
        converted_result = []
        for v in result:
            converted_value = getattr(self, "_convert_type_%s" % settings_type)(
                v, template
            )
            if isinstance(converted_value, list):
                converted_result += converted_value
            else:
                converted_result.append(converted_value)
        result = list(OrderedDict.fromkeys(converted_result))
        if isinstance(result, list) and len(result) == 1:
            result = result[0]
        return result

    def _convert_type_str(self, value, template):
        val = value.strip()
        if self.split_separator:
            return [v.strip() for v in val.split(self.split_separator)]
        return val

    def _convert_type_int(self, value, template):
        return int(self._convert_type_float(value, template))

    def _convert_type_float(self, value, template):
        if not value.strip():
            return 0.0
        assert (
            value.count(self.decimal_separator or template.decimal_separator) < 2
        ), "Decimal separator cannot be present several times"
        # replace decimal separator by a |
        amount_pipe = value.replace(
            self.decimal_separator or template.decimal_separator, "|"
        )
        # remove all possible thousands separators
        amount_pipe_no_thousand_sep = re.sub(r"[.,'\s]", "", amount_pipe)
        # put dot as decimal sep
        return float(amount_pipe_no_thousand_sep.replace("|", "."))

    def _convert_type_date(self, value, template):
        lang = self.env["res.lang"]._lang_get(template.lang)
        return dateparser.parse(
            value,
            date_formats=[self.date_format],
            locales=[lang.iso_code.replace("_", "-")],
        )


class Pdf2dataTemplateKeyword(models.Model):
    _name = "pdf2data.template.keyword"

    template_id = fields.Many2one(
        "pdf2data.template", required=True, ondelete="cascade"
    )
    keyword = fields.Char(required=True)
    exclude = fields.Boolean()


class Pdf2dataTemplateReplace(models.Model):
    _name = "pdf2data.template.replace"

    template_id = fields.Many2one("pdf2dta.template", required=True, ondelete="cascade")
    from_char = fields.Char()
    to_char = fields.Char()


# TODO: Remove
class Pdf2dataTemplateType(models.Model):

    _name = "pdf2data.template.type"
    _description = "Pdf2data Template Type"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
