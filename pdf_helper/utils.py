# Copyright 2015-2021 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from io import BytesIO
from struct import error as StructError

from lxml import etree

from odoo.tools.pdf import OdooPdfFileReader, PdfReadError

_logger = logging.getLogger(__name__)


class PDFParser:
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file

    def get_xml_files(self):
        """Parse PDF files to extract XML content.

        :param pdf_file: binary PDF file content
        :returns: a dict like {$filename: $parsed_xml_file_obj}.
        """
        res = {}
        with BytesIO(self.pdf_file) as buffer:
            pdf_reader = OdooPdfFileReader(buffer, strict=False)

            # Process embedded files.
            for xml_name, content in pdf_reader.getAttachments():
                try:
                    res[xml_name] = etree.fromstring(content)
                except Exception:
                    _logger.debug("Non XML file found in PDF")
            if res:
                _logger.debug("Valid XML files found in PDF: %s", list(res.keys()))
        return res

    def get_xml_files_swallable_exceptions(self):
        return (NotImplementedError, StructError, PdfReadError)
