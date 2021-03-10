# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class EdiExchangeConsumerTest(models.Model):
    _name = "edi.exchange.consumer.test"
    _inherit = ["edi.exchange.consumer.mixin"]
    _description = "Model used only for test"

    name = fields.Char()

    def _get_edi_exchange_record_name(self, exchange_record):
        return self.id
