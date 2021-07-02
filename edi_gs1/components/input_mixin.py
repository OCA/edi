# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class GS1InputMessageMixin(AbstractComponent):
    """Common gs1 input mixin.
    """

    _name = "edi.gs1.input.mixin"
    _inherit = ["edi.component.input.mixin"]
    _xsd_schema_path = None

    def process(self):
        schema_path = self._xsd_schema_path or self.work.schema_path
        handler = self.backend._find_component(
            self.backend._name,
            ["edi.xml"],
            work_ctx={"schema_path": schema_path},
            safe=False,
        )
        data = handler.parse_xml(self.exchange_record._get_file_content())
        self._process_data(data)
        return True

    def _process_data(self, data):
        NotImplementedError()
