# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import os
from collections import OrderedDict
from tempfile import NamedTemporaryFile

import dateparser

from odoo import api, fields, models

_logger = logging.getLogger(__name__)
import re

import yaml
from unidecode import unidecode

try:
    import fitz
except ImportError:
    _logger.debug("Cannot import PyMuPDF")


class Pdf2dataTemplate(models.Model):
    _name = "pdf2data.template"
    _description = "Pdf2data Template"
    _order = "sequence"

    name = fields.Char()
    code = fields.Char(related="type_id.code")
    type_id = fields.Many2one("pdf2data.template.type", required=True)
    pdf2data_template_yml = fields.Text(
        compute="_compute_template_yml", inverse="_inverse_template_yml"
    )
    pdf2data_template_dict = fields.Serialized()
    pdf_file = fields.Binary(attachment=True)
    pdf_filename = fields.Char()
    file_result = fields.Char(readonly=True)
    file_processed_result = fields.Html(readonly=True)
    sequence = fields.Integer(default=20)
    extracted_text = fields.Text(readonly=True)

    @api.depends("pdf2data_template_dict")
    def _compute_template_yml(self):
        for record in self:
            record.pdf2data_template_yml = yaml.dump(record.pdf2data_template_dict)

    def _inverse_template_yml(self):
        for record in self:
            tpl = yaml.load(record.pdf2data_template_yml)
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

    def _parse_pdf(self, data):
        data_file = NamedTemporaryFile(
            delete=False, prefix="odoo-simple-pdf-", suffix=".pdf"
        )
        try:
            data_file.write(base64.b64decode(data))
            data_file.close()
            extracted_str = ""
            doc = fitz.open(data_file.name)
            for page in doc:
                extracted_str += page.getText("text")
        finally:
            os.unlink(data_file.name)
        _logger.debug("START pdftotext result ===========================")
        _logger.debug(extracted_str)
        _logger.debug("END pdftotext result =============================")

        _logger.debug("Testing {} template files".format(len(self)))
        for template in self:
            print(extracted_str)
            optimized_str = self.prepare_input(extracted_str)
            print(optimized_str)
            if self.matches_input(optimized_str):
                return optimized_str, self.extract_data(optimized_str), template
        return False, False, False

    def prepare_input(self, extracted_str):
        """
        Input raw string and do transformations, as set in template file.
        """

        # Remove withspace
        if self.pdf2data_template_dict["options"].get("remove_whitespace"):
            optimized_str = re.sub(" +", "", extracted_str)
        else:
            optimized_str = extracted_str

        # Remove accents
        if self.pdf2data_template_dict["options"].get("remove_accents"):
            optimized_str = unidecode(optimized_str)

        # convert to lower case
        if self.pdf2data_template_dict["options"].get("lowercase"):
            optimized_str = optimized_str.lower()

        # specific replace
        for replace in self.pdf2data_template_dict["options"].get("replace", []):
            assert (
                len(replace) == 2
            ), "A replace should be a list of exactly 2 elements."
            optimized_str = re.sub(replace[0], replace[1], optimized_str)

        return optimized_str

    def matches_input(self, optimized_str):
        """See if string matches all keyword patterns and no exclude_keyword patterns set in template file.
        Args:
        optimized_str: String of the text from OCR of the pdf after applying options defined in the template.
        Return:
        Boolean
            - True if all keywords are found and none of the exclude_keywords are found.
            - False if either not all keywords are found or at least one exclude_keyword is found."""
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

    def extract_data(self, optimized_str):

        """
        Given a template file and a string, extract matching data fields.
        """

        _logger.debug("START optimized_str ========================")
        _logger.debug(optimized_str)
        _logger.debug("END optimized_str ==========================")
        _logger.debug(
            "Date parsing: languages=%s date_formats=%s",
            self.pdf2data_template_dict["options"].get("languages"),
            self.pdf2data_template_dict["options"].get("date_formats"),
        )
        _logger.debug(
            "Float parsing: decimal separator=%s",
            self.pdf2data_template_dict["options"].get("decimal_separator", "."),
        )
        _logger.debug("keywords=%s", self.pdf2data_template_dict["keywords"])
        _logger.debug(self.pdf2data_template_dict)

        # Try to find data for each field.
        output = {}
        output["issuer"] = self.name

        for k, v in self.pdf2data_template_dict["fields"].items():
            if isinstance(v, dict):
                if "parser" in v:
                    if hasattr(self, "_parse_%s" % v["parser"]):
                        parser = getattr(self, "_parse_%s" % v["parser"])
                        value = parser(k, v, optimized_str)
                        if value is not None:
                            output[k] = value
                        else:
                            _logger.error(
                                "Failed to parse field %s with parser %s",
                                k,
                                v["parser"],
                            )
                    else:
                        _logger.warning(
                            "Field %s has unknown parser %s set", k, v["parser"]
                        )
                else:
                    _logger.warning("Field %s doesn't have parser specified", k)
            elif k.startswith("static_"):
                _logger.debug("field=%s | static value=%s", k, v)
                output[k.replace("static_", "")] = v
            else:
                # Legacy syntax support (backward compatibility)
                result = None
                if k.startswith("sum_amount") and type(v) is list:
                    k = k[4:]
                    result = self._parse_regex(
                        k,
                        {"regex": v, "type": "float", "group": "sum"},
                        optimized_str,
                        True,
                    )
                elif k.startswith("date") or k.endswith("date"):
                    result = self._parse_regex(
                        k, {"regex": v, "type": "date"}, optimized_str, True
                    )
                elif k.startswith("amount"):
                    result = self._parse_regex(
                        k, {"regex": v, "type": "float"}, optimized_str, True
                    )
                else:
                    result = self._parse_regex(k, {"regex": v}, optimized_str, True)

                if result is None:
                    _logger.warning("regexp for field %s didn't match", k)
                else:
                    output[k] = result

        output["currency"] = self.pdf2data_template_dict["options"].get(
            "currency", "EUR"
        )

        # Run plugins:
        # for plugin_keyword, plugin_func in PLUGIN_MAPPING.items():
        #    if plugin_keyword in self.keys():
        #        plugin_func.extract(self, optimized_str, output)

        # If required fields were found, return output, else log error.
        required_fields = self.pdf2data_template_dict["options"].get(
            "required_fields", []
        )

        if set(required_fields).issubset(output.keys()):
            output["desc"] = "Invoice from %s" % (self.name)
            _logger.debug(output)
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

    def _parse_regex(self, field, settings, content, legacy=False):
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

        if "type" in settings:
            for k, v in enumerate(result):
                result[k] = self.coerce_type(v, settings["type"])

        if "group" in settings:
            if settings["group"] == "sum":
                result = sum(result)
            else:
                _logger.warning("Unsupported grouping method: " + settings["group"])
                return None
        else:
            # Remove duplicates maintaining the order by default (it's more
            # natural). Don't do that for legacy parsing to keep backward
            # compatibility.
            if legacy:
                result = list(set(result))
            else:
                result = list(OrderedDict.fromkeys(result))

        if isinstance(result, list) and len(result) == 1:
            result = result[0]

        return result

    def coerce_type(self, value, target_type):
        if target_type == "int":
            if not value.strip():
                return 0
            return int(self.parse_number(value))
        elif target_type == "float":
            if not value.strip():
                return 0.0
            return float(self.parse_number(value))
        elif target_type == "date":
            return self.parse_date(value)
        assert False, "Unknown type"

    def parse_number(self, value):
        assert (
            value.count(self.options["decimal_separator"]) < 2
        ), "Decimal separator cannot be present several times"
        # replace decimal separator by a |
        amount_pipe = value.replace(
            self.pdf2data_template_dict["options"].get("decimal_separator", "."), "|"
        )
        # remove all possible thousands separators
        amount_pipe_no_thousand_sep = re.sub(r"[.,'\s]", "", amount_pipe)
        # put dot as decimal sep
        return float(amount_pipe_no_thousand_sep.replace("|", "."))

    def parse_date(self, value):
        """Parses date and returns date after parsing"""
        res = dateparser.parse(
            value,
            date_formats=self.pdf2data_template_dict["options"].get("date_formats", []),
            languages=self.pdf2data_template_dict["options"].get("languages", []),
        )
        _logger.debug("result of date parsing=%s", res)
        return res

    def check_pdf(self):
        self.ensure_one()
        extracted_text, data, template = self._parse_pdf(self.pdf_file)
        if not template:
            self.write(
                {
                    "file_result": False,
                    "file_processed_result": "Data cannot be processed",
                    "extracted_text": "No text extracted",
                }
            )
            return
        self.extracted_text = extracted_text
        self.file_result = data
        backend = self.env.ref("edi_pdf2data.pdf2data_backend")
        component = backend._find_component(
            self._name,
            ["process_data"],
            backend_type=backend.backend_type_id.code,
            process_type=self.type_id.code,
        )
        if component and hasattr(component, "preview_data"):
            self.file_processed_result = component.preview_data(data, self)
        else:
            self.file_processed_result = self._preview_data(data)

    def _preview_data(self, data):
        result = ""
        for key in data:
            value = data[key]
            if isinstance(value, list):
                result += "<li>{}:{}</li>".format(
                    key,
                    "".join(
                        "<ul><li>Item: %s</li></ul>" % self._preview_data(val)
                        for val in value
                    ),
                )
            else:
                result += "<li>{}: {}</li>".format(key, value)
        return "<ul>%s</ul>" % result


class Pdf2dataTemplateType(models.Model):

    _name = "pdf2data.template.type"
    _description = "Pdf2data Template Type"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
