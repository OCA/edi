# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# Copyright 2020 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from io import BytesIO

from lxml import etree

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools import file_open

logger = logging.getLogger(__name__)


class BaseUbl(models.AbstractModel):
    _name = "base.ubl"
    _description = "Common methods to generate and parse UBL XML files"

    @api.model
    def _ubl_check_xml_schema(self, xml_string, document, version="2.1"):
        """Validate the XML file against the XSD"""
        xsd_file = f"base_ubl/data/xsd-{version}/maindoc/UBL-{document}-{version}.xsd"
        xsd_etree_obj = etree.parse(file_open(xsd_file))
        official_schema = etree.XMLSchema(xsd_etree_obj)
        try:
            t = etree.parse(BytesIO(xml_string))
            official_schema.assertValid(t)
        except Exception as e:
            # if the validation of the XSD fails, we arrive here
            logger = logging.getLogger(__name__)
            logger.warning("The XML file is invalid against the XML Schema Definition")
            logger.warning(xml_string)
            logger.warning(e)
            raise UserError(
                self.env._(
                    "The UBL XML file is not valid against the official "
                    "XML Schema Definition. The XML file and the "
                    "full error have been written in the server logs. "
                    "Here is the error, which may give you an idea on the "
                    "cause of the problem : %(error)s.",
                    error=str(e),
                )
            ) from e
        return True

    @api.model
    def _ubl_get_nsmap_namespace(self, doc_name, version="2.1"):
        nsmap = {
            None: "urn:oasis:names:specification:ubl:schema:xsd:" + doc_name,
            "cac": "urn:oasis:names:specification:ubl:"
            "schema:xsd:CommonAggregateComponents-2",
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:"
            "CommonBasicComponents-2",
        }
        ns = {
            "cac": "{urn:oasis:names:specification:ubl:schema:xsd:"
            "CommonAggregateComponents-2}",
            "cbc": "{urn:oasis:names:specification:ubl:schema:xsd:"
            "CommonBasicComponents-2}",
        }
        return nsmap, ns
