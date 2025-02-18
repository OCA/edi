# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.core import AbstractComponent


class EDIBackendInputComponentMixin(AbstractComponent):
    """Generate input content."""

    _name = "edi.component.input.mixin"
    _inherit = "edi.component.mixin"

    def process(self):
        raise NotImplementedError()


class EDIBackendReceiveComponentMixin(AbstractComponent):
    _name = "edi.component.receive.mixin"
    _inherit = "edi.component.mixin"

    def receive(self):
        raise NotImplementedError()
