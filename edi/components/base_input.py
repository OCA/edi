# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class EDIBackendInputComponentMixin(AbstractComponent):
    """Generate input content.
    """

    _name = "edi.component.input.mixin"
    _inherit = "edi.component.mixin"

    def process(self):
        raise NotImplementedError()


# class EDIBackendCheckComponentMixin(AbstractComponent):

#     _name = "edi.component.check.mixin"
#     _inherit = "edi.component.mixin"

#     def check(self):
#         raise NotImplementedError()
