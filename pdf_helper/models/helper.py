# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import api, models

from ..utils import PDFParser

_logger = logging.getLogger(__name__)


class PDFHelper(models.AbstractModel):
    _name = "pdf.helper"
    _description = "PDF Helper"

    _PDF_PARSER_KLASS = PDFParser

    @api.model
    def pdf_get_xml_files(self, pdf_file):
        """Extract XML attachments from pdf

        :param pdf_file: binary PDF file content
        :returns: a dict like {$filename: $parsed_xml_file_obj}.
        """
        parser = self._PDF_PARSER_KLASS(pdf_file)
        try:
            return parser.get_xml_files()
        except parser.get_xml_files_swallable_exceptions() as err:
            _logger.error("PDF file parsing failed: %s", str(err))
            return {}
