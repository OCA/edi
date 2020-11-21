# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class EDIBackendComponentMixin(AbstractComponent):

    _name = "edi.component.mixin"
    _collection = "edi.backend"

    @property
    def exchange_record(self):
        return self.work.exchange_record

    @property
    def backend(self):
        return self.work.backend


class EDIBackendOutputComponentMixin(AbstractComponent):
    """Generate output content.
    """

    _name = "edi.component.output.mixin"
    _inherit = "edi.component.mixin"

    def generate(self):
        raise NotImplementedError()


class EDIBackendSendComponentMixin(AbstractComponent):
    """Send output records.
    """

    _name = "edi.component.send.mixin"
    _inherit = "edi.component.mixin"

    def send(self):
        raise NotImplementedError()


class EDIBackendCheckComponentMixin(AbstractComponent):

    _name = "edi.component.check.mixin"
    _inherit = "edi.component.mixin"

    def check(self):
        raise NotImplementedError()


class EDIBackendCheckComponentProcess(AbstractComponent):

    _name = "edi.component.process.mixin"
    _inherit = "edi.component.mixin"

    def process(self):
        raise NotImplementedError()
