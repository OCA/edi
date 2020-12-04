# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class GS1InputMessageMixin(AbstractComponent):
    """Common gs1 input mixin.
    """

    _name = "edi.gs1.input.mixin"
    _inherit = ["edi.component.input.mixin"]

    def process(self):
        handler = self.backend._find_component(
            ["edi.xml"], work_ctx={"schema_path": self.work.schema_path}, safe=False
        )
        data = handler.parse_xml(self.exchage_record._get_file_content())
        self._process_data(data)
        return True

    def _process_data(self, data):
        NotImplementedError()
