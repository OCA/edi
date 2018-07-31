# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, tools, _
from odoo.exceptions import UserError
from lxml import etree
from StringIO import StringIO
import logging
logger = logging.getLogger(__name__)


class BaseFacturX(models.AbstractModel):
    _name = 'base.facturx'
    _description = 'Common methods to generate and parse Factur-X invoices'

    @api.model
    def _cii_check_xml_schema(self, xml_string, flavor, level=False):
        '''Validate the XML file against the XSD'''
        if flavor in ('factur-x', 'facturx'):
            facturx_level2xsd = {
                'minimum': 'FACTUR-X_BASIC-WL.xsd',
                'basicwl': 'FACTUR-X_BASIC-WL.xsd',
                'basic': 'FACTUR-X_EN16931.xsd',
                'en16931': 'FACTUR-X_EN16931.xsd',  # comfort
                False: 'FACTUR-X_EN16931.xsd',
                }
            if level not in facturx_level2xsd:
                raise UserError(_(
                    "Wrong level '%s' for Factur-X invoice.") % level)
            xsd_filename = facturx_level2xsd[level]
            xsd_file = 'base_zugferd/data/xsd-factur-x/%s' % xsd_filename
        elif flavor == 'zugferd':
            xsd_file = 'base_zugferd/data/xsd-zugferd/ZUGFeRD1p0.xsd'
        xsd_etree_obj = etree.parse(tools.file_open(xsd_file))
        official_schema = etree.XMLSchema(xsd_etree_obj)
        try:
            t = etree.parse(StringIO(xml_string))
            official_schema.assertValid(t)
        except Exception, e:
            # if the validation of the XSD fails, we arrive here
            logger.warning(
                "The XML file is invalid against the XML Schema Definition")
            logger.warning(xml_string)
            logger.warning(e)
            raise UserError(_(
                "The %s XML file is not valid against the official "
                "XML Schema Definition. The XML file and the "
                "full error have been written in the server logs. "
                "Here is the error, which may give you an idea on the "
                "cause of the problem : %s.")
                % (flavor.capitalize(), unicode(e)))
        return True
