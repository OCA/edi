# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import AbstractComponent


class GS1OutputMessageMixin(AbstractComponent):
    """Common gs1 output mixin.
    """

    _name = "edi.gs1.output.mixin"
    _inherit = ["edi.output.info.mixin"]
    _work_context_validate_attrs = [
        "exchange_record",
        "sender",
        "receiver",
    ]

    def _document_action_code(self):
        # Brand new file
        code = "ADD"
        if self.replace_existing:
            code = "CHANGE_BY_REFRESH"
        return code
