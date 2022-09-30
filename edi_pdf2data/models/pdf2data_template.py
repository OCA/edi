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
    pdf2data_template_yml = fields.Text(
        compute="_compute_template_yml", inverse="_inverse_template_yml"
    )
    pdf2data_template_dict = fields.Serialized()
    pdf2data_options_dict = fields.Serialized()
    pdf_file = fields.Binary(attachment=True)
    pdf_filename = fields.Char()
    file_result = fields.Char(readonly=True)
    sequence = fields.Integer(default=20)
    extracted_text = fields.Text(readonly=True)

    @api.depends("pdf2data_template_dict")
    def _compute_template_yml(self):
        for record in self:
            record.pdf2data_template_yml = yaml.dump(record.pdf2data_template_dict)

    @api.model
    def _get_pdf2data_options(self):
        return {
            "remove_whitespace": False,
            "remove_accents": False,
            "lowercase": False,
            "currency": "EUR",
            "date_formats": [],
            "language": "en",
            "replace": [],
            "required_fields": [],
        }

    def _inverse_template_yml(self):
        for record in self:
            tpl = yaml.load(record.pdf2data_template_yml, Loader=yaml.SafeLoader)
            assert "keywords" in tpl.keys(), "Missing keywords field."
            # Keywords as list, if only one.
            if type(tpl["keywords"]) is not list:
                tpl["keywords"] = [tpl["keywords"]]
            # Define excluded_keywords as empty list if not provided
            # Convert to list if only one provided
            if (
                "exclude_keywords" in tpl.keys()
                and type(tpl["exclude_keywords"]) is not list
            ):
                tpl["exclude_keywords"] = [tpl["exclude_keywords"]]
            record.pdf2data_template_dict = tpl
            options = self._get_pdf2data_options()
            options.update(tpl.get("options", {}))
            record.pdf2data_options_dict = options

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
        _logger.debug("START pdftotext result ===========================")
        _logger.debug(extracted_str)
        _logger.debug("END pdftotext result =============================")

        _logger.debug("Testing {} template files".format(len(self)))
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
        if self.pdf2data_options_dict["remove_whitespace"]:
            optimized_str = re.sub(" +", "", extracted_str)
        else:
            optimized_str = extracted_str

        # Remove accents
        if self.pdf2data_options_dict["remove_accents"]:
            optimized_str = unidecode(optimized_str)

        # convert to lower case
        if self.pdf2data_options_dict["lowercase"]:
            optimized_str = optimized_str.lower()

        # specific replace
        for replace in self.pdf2data_options_dict["replace"]:
            assert (
                len(replace) == 2
            ), "A replace should be a list of exactly 2 elements."
            optimized_str = re.sub(replace[0], replace[1], optimized_str)

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
            [
                re.search(keyword, optimized_str)
                for keyword in self.pdf2data_template_dict["keywords"]
            ]
        ):
            # All keyword patterns matched
            exclude_keywords = self.pdf2data_template_dict.get("exclude_keywords")
            if exclude_keywords:
                if any(
                    [
                        re.search(exclude_keyword, optimized_str)
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

        _logger.debug("START optimized_str ========================")
        _logger.debug(optimized_str)
        _logger.debug("END optimized_str ==========================")
        _logger.debug(
            "Date parsing: language=%s date_formats=%s",
            self.pdf2data_options_dict["language"],
            self.pdf2data_options_dict["date_formats"],
        )
        _logger.debug("keywords=%s", self.pdf2data_template_dict["keywords"])
        _logger.debug(self.pdf2data_template_dict)

        # Try to find data for each field.
        output = {
            "issuer": self.name,
            "currency": self.pdf2data_options_dict["currency"],
        }

        output.update(
            self._extract_fields(optimized_str, self.pdf2data_template_dict["fields"])
        )

        # Run plugins:
        # for plugin_keyword, plugin_func in PLUGIN_MAPPING.items():
        #    if plugin_keyword in self.keys():
        #        plugin_func.extract(self, optimized_str, output)

        # If required fields were found, return output, else log error.
        required_fields = self.pdf2data_options_dict["required_fields"]

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

    def _extract_fields(self, optimized_str, fields):
        output = {}
        for field, field_settings in fields.items():
            if isinstance(field_settings, dict):
                parser_key = field_settings.get("parser", "regex")
                if hasattr(self, "_parse_%s" % parser_key):
                    parser = getattr(self, "_parse_%s" % parser_key)
                    value = parser(field, field_settings, optimized_str)
                    if value is not None:
                        output[field] = value
                    else:
                        _logger.error(
                            "Failed to parse field %s with parser %s",
                            field,
                            field_settings["parser"],
                        )
                else:
                    _logger.warning(
                        "Field %s has unknown parser %s set", field, parser_key
                    )
        return output

    def _parse_regex(self, field, settings, content):
        if "regex" not in settings:
            _logger.warning('Field "%s" doesn\'t have regex specified', field)
            return None

        if isinstance(settings["regex"], list):
            regexes = settings["regex"]
        else:
            regexes = [settings["regex"]]

        result = []
        for regex in regexes:
            matches = re.findall(regex, content)
            _logger.debug(
                "field=%s | regex=%s | matches=%s", field, settings["regex"], matches
            )
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
        settings_type = settings.get("type", "str")
        converted_result = []
        for v in result:
            if hasattr(self, "_convert_type_%s" % settings_type):
                converted_value = getattr(self, "_convert_type_%s" % settings_type)(
                    v, settings
                )
                if isinstance(converted_value, list):
                    converted_result += converted_value
                else:
                    converted_result.append(converted_value)
            else:
                converted_result.append(v)
                _logger.warning("Unsupported type %s" % settings_type)
        result = converted_result
        if "group" in settings:
            if settings["group"] == "sum":
                result = sum(result)
            else:
                _logger.warning("Unsupported grouping method: " + settings["group"])
                return None
        else:
            result = list(OrderedDict.fromkeys(result))
        if isinstance(result, list) and len(result) == 1:
            result = result[0]
        return result

    def _parse_static(self, field, settings, content):
        if "value" not in settings:
            _logger.warning("Field %s doesn't have value key defined" % field)
        return settings["value"]

    @api.model
    def _default_line_settings(self):
        return {"line_separator": r"\n"}

    def _parse_line(self, field, settings, content):
        line_settings = self._default_line_settings()
        line_settings.update(settings)
        assert "start_block" in line_settings, "Lines block start regex missing"
        assert "end_block" in line_settings, "Lines block end regex missing"
        assert "start" in line_settings, "Start regex missing"
        assert "end" in line_settings, "End regex missing"
        assert "fields" in line_settings, "Fields missing"
        start = re.search(line_settings["start_block"], content)
        end = re.search(line_settings["end_block"], content)
        if not start or not end:
            _logger.warning(f"No lines found. Start match: {start}. End match: {end}")
            return
        content = content[start.end() : end.start()]
        lines = []
        line_content = []
        for line in re.split(line_settings["line_separator"], content):
            if not line.strip("").strip("\n").strip("\r") or not line:
                continue
            if not line_content and re.search(settings["start"], line):
                line_content.append(line)
                continue
            if not line_content:
                continue
            line_content.append(line)
            if re.search(settings["end"], line):
                lines.append(
                    self._extract_fields(
                        line_settings["line_separator"].join(line_content),
                        line_settings["fields"],
                    )
                )
                line_content = []
        return lines

    def _convert_type_str(self, value, settings):
        val = value.strip()
        if settings.get("split_separator", False):
            return [v.strip() for v in val.split(settings["split_separator"])]
        return val

    def _convert_type_int(self, value, settings):
        return int(self._convert_type_float(value, settings))

    def _convert_type_float(self, value, settings):
        if not value.strip():
            return 0.0
        assert (
            value.count(self.pdf2data_options_dict["decimal_separator"]) < 2
        ), "Decimal separator cannot be present several times"
        # replace decimal separator by a |
        amount_pipe = value.replace(
            self.pdf2data_options_dict["decimal_separator"], "|"
        )
        # remove all possible thousands separators
        amount_pipe_no_thousand_sep = re.sub(r"[.,'\s]", "", amount_pipe)
        # put dot as decimal sep
        return float(amount_pipe_no_thousand_sep.replace("|", "."))

    def _convert_type_date(self, value, settings):
        return dateparser.parse(
            value,
            date_formats=self.pdf2data_options_dict["date_formats"],
            languages=[self.pdf2data_options_dict["language"]],
        )

    def check_pdf(self):
        self.ensure_one()
        extracted_text, data, template = self._extract_pdf(self.pdf_file)
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


class Pdf2dataTemplateType(models.Model):

    _name = "pdf2data.template.type"
    _description = "Pdf2data Template Type"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
