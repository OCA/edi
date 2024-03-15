# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.core import AbstractComponent


class EDIBackendOutputComponentMixin(AbstractComponent):
    """Generate output content."""

    _name = "edi.component.output.mixin"
    _inherit = "edi.component.mixin"
    _usage = "edi.output.generate.*"

    def generate(self):
        raise NotImplementedError()


class EDIBackendSendComponentMixin(AbstractComponent):
    """Send output records."""

    _name = "edi.component.send.mixin"
    _inherit = "edi.component.mixin"
    _usage = "edi.output.send.*"

    def send(self):
        raise NotImplementedError()


class EDIBackendCheckComponentMixin(AbstractComponent):

    _name = "edi.component.check.mixin"
    _inherit = "edi.component.mixin"
    _usage = "edi.output.check.*"

    def check(self):
        raise NotImplementedError()
