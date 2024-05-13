# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import logging

from pypdf.errors import PdfReadError

from odoo import models

from ..utils import PDFParser

_logger = logging.getLogger(__name__)


class PDFHelper(models.AbstractModel):
    _name = "pdf.helper"
    _description = "PDF Helper"

    _PDF_PARSER_KLASS = PDFParser

    def pdf_get_xml_files(self, pdf_file):
        parser = self._PDF_PARSER_KLASS(pdf_file)
        try:
            return parser.get_xml_files()
        except self._pdf_get_xml_files_swallable_exceptions() as err:
            # TODO: can't we catch specific exceptions?
            # This try/except block was added to reflect what done
            # in base_business_document_import till now.
            _logger.error("PDF file parsing failed: %s", str(err))
            return {}

    def _pdf_get_xml_files_swallable_exceptions(self):
        return (KeyError, PdfReadError)
