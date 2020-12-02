# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tools import DotDict

from odoo.addons.component.core import AbstractComponent


class GS1OutputMessageMixin(AbstractComponent):
    """Common gs1 output mixin.
    """

    _name = "edi.gs1.output.mixin"
    _inherit = [
        "edi.output.mixin",
    ]
    _work_context_validate_attrs = [
        "record",
        "sender",
        "receiver",
    ]

    def generate_info(self):
        return DotDict(self._generate_info())

    def _generate_info(self):
        raise NotImplementedError("You must provide `_generate_info`")

    @property
    def replace_existing(self):
        """Pass `replace_existing` to work context to change this value."""
        return getattr(self.work, "replace_existing", False)

    def _document_action_code(self):
        # Brand new file
        code = "ADD"
        if self.replace_existing:
            code = "CHANGE_BY_REFRESH"
        return code
