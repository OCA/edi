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
    import PyPDF2
except ImportError:
    _logger.debug("Cannot import PyPDF2")


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
            xmlfiles = self._extract_xml_files(fd)
            for filename, xml_obj in xmlfiles.items():
                root = self._extract_xml_root(xml_obj)
                if root is None or not len(root):
                    continue
                res[filename] = root
        if res:
            _logger.debug("Valid XML files found in PDF: %s", list(res.keys()))
        return res

    def _extract_xml_files(self, fd):
        pdf = PyPDF2.PdfFileReader(fd)
        _logger.debug("pdf.trailer=%s", pdf.trailer)
        pdf_root = pdf.trailer["/Root"]
        _logger.debug("pdf_root=%s", pdf_root)
        # TODO add support for /Kids
        embeddedfiles = pdf_root["/Names"]["/EmbeddedFiles"]["/Names"]
        i = 0
        xmlfiles = {}  # key = filename, value = PDF obj
        for embeddedfile in embeddedfiles[:-1]:
            mime_res = mimetypes.guess_type(embeddedfile)
            if mime_res and mime_res[0] in ["application/xml", "text/xml"]:
                xmlfiles[embeddedfile] = embeddedfiles[i + 1]
            i += 1
        _logger.debug("xmlfiles=%s", xmlfiles)
        return xmlfiles

    def _extract_xml_root(self, xml_obj):
        xml_root = None
        try:
            xml_file_dict = xml_obj.getObject()
            _logger.debug("xml_file_dict=%s", xml_file_dict)
            xml_string = xml_file_dict["/EF"]["/F"].getData()
            xml_root = etree.fromstring(xml_string)
        except Exception as err:
            # TODO: can't we catch specific exceptions?
            _logger.debug("_pdf_extract_xml_root failed: %s", str(err))
        return xml_root
