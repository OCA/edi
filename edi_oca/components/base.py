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

    @property
    def record(self):
        return self.work.exchange_record.record
