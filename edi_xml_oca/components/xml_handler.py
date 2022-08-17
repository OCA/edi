# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import io
from contextlib import closing

import xmlschema

from odoo import modules
from odoo.tools import DotDict

from odoo.addons.component.core import Component


class XMLHandler(Component):
    """Validate and parse XML."""

    _name = "edi.xml.handler"
    _inherit = "edi.component.base.mixin"
    _usage = "edi.xml"

    _work_context_validate_attrs = ["schema_path"]

    def __init__(self, work_context):
        super().__init__(work_context)
        for key in self._work_context_validate_attrs:
            if not hasattr(work_context, key):
                raise AttributeError(f"`{key}` is required for this component!")

        self.schema = xmlschema.XMLSchema(self._get_xsd_schema_path())

    def _get_xsd_schema_path(self):
        """Lookup for XSD schema."""
        try:
            mod_name, path = self.work.schema_path.split(":")
        except ValueError:
            raise ValueError("Path must be in the form `module:path`")
        return modules.get_resource_path(mod_name, path)

    def _parse_xml(self, file_obj, **kw):
        """Read xml_content and return a data dict.

        :param file_obj: file obj of XML file
        """
        return DotDict(self.schema.to_dict(file_obj, **kw))

    def parse_xml(self, file_content, **kw):
        """Read XML content.
        :param file_content: str of XML file
        :return: dict with final data
        """
        with closing(io.StringIO(file_content)) as fd:
            return self._parse_xml(fd)

    def validate(self, xml_content, raise_on_fail=False):
        """Validate XML content against XSD schema.

        Raises `XMLSchemaValidationError` if `raise_on_fail` is True.

        :param xml_content: str containing xml data to validate
        :raise_on_fail: turn on/off validation error exception on fail

        :return:
            * None if validation is ok
            * error string if `raise_on_fail` is False
        """
        try:
            return self.schema.validate(xml_content)
        except self._validate_swallable_exceptions() as err:
            if raise_on_fail:
                raise
            return str(err)

    def _validate_swallable_exceptions(self):
        return (
            xmlschema.exceptions.XMLSchemaValueError,
            xmlschema.validators.exceptions.XMLSchemaValidationError,
        )
