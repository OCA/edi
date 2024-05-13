# Copyright 2015-2021 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import mimetypes
from io import BytesIO

from lxml import etree

_logger = logging.getLogger(__name__)

try:
    import pypdf
except ImportError:
    _logger.debug("Cannot import pypdf")


class PDFParser:
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file

    def get_xml_files(self):
        """Parse PDF files to extract XML content.

        :param pdf_file: binary PDF file content
        :returns: a dict like {$filename: $parsed_xml_file_obj}.
        """
        res = {}
        with BytesIO(self.pdf_file) as fd:
            res = self._extract_xml_files(fd)
        if res:
            _logger.debug("Valid XML files found in PDF: %s", list(res.keys()))
        return res

    def _extract_xml_files(self, fd):
        reader = pypdf.PdfReader(fd)
        # attachment parsing via pypdf doesn't support /Kids
        # cf my bug report https://github.com/py-pdf/pypdf/issues/2087
        xmlfiles = {}
        for filename, content_list in reader.attachments.items():
            _logger.debug("Attachment %s found in PDF", filename)
            mime_res = mimetypes.guess_type(filename)
            if mime_res and mime_res[0] in ["application/xml", "text/xml"]:
                try:
                    _logger.debug("Trying to parse XML attachment %s", filename)
                    xml_root = etree.fromstring(content_list[0])
                    if len(xml_root) > 0:
                        _logger.info("Valid XML file %s found in attachments", filename)
                        xmlfiles[filename] = xml_root
                    else:
                        _logger.warning("XML file %s is empty", filename)
                except Exception as err:
                    _logger.warning(
                        "Failed to parse XML file %s. Error: %s", filename, str(err)
                    )
        return xmlfiles
