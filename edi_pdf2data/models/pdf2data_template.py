# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import os
from tempfile import NamedTemporaryFile

from odoo import fields, models

_logger = logging.getLogger(__name__)
try:
    from invoice2data.extract.invoice_template import InvoiceTemplate
    from invoice2data.extract.loader import ordered_load
except ImportError:
    _logger.debug("Cannot import invoice2data")

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
    pdf2data_template_yml = fields.Text()
    pdf_file = fields.Binary(attachment=True)
    pdf_filename = fields.Char()
    file_result = fields.Char(readonly=True)
    file_processed_result = fields.Html(readonly=True)
    sequence = fields.Integer(default=20)
    extracted_text = fields.Text(readonly=True)

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
            data = template.pdf2data_template_yml
            tpl = ordered_load(data)
            tpl["template_name"] = template.name

            # Test if all required fields are in template:
            assert "keywords" in tpl.keys(), "Missing keywords field."
            # Keywords as list, if only one.
            if type(tpl["keywords"]) is not list:
                tpl["keywords"] = [tpl["keywords"]]
            # Define excluded_keywords as empty list if not provided
            # Convert to list if only one provided
            if "exclude_keywords" not in tpl.keys():
                tpl["exclude_keywords"] = []
            elif type(tpl["exclude_keywords"]) is not list:
                tpl["exclude_keywords"] = [tpl["exclude_keywords"]]

            t = InvoiceTemplate(tpl)
            optimized_str = t.prepare_input(extracted_str)
            if t.matches_input(optimized_str):
                return optimized_str, t.extract(optimized_str), template
        return False, False, False

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
