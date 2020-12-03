# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class EDIBackendValidateComponentMixin(AbstractComponent):
    """Validate exchange data.
    """

    _name = "edi.component.validate.mixin"
    _inherit = "edi.component.mixin"
    _usage = "edi.validate.*"

    def validate(self, value=None):
        raise NotImplementedError()
