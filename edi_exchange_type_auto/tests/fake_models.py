# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EdiAutoExchangeConsumerTest(models.Model):
    _name = "edi.auto.exchange.consumer.test"
    _inherit = [
        "edi.auto.exchange.consumer.mixin",
    ]
    _description = _name

    name = fields.Char()
    state = fields.Char()
    number = fields.Integer()
    partner_id = fields.Many2one("res.partner")

    _edi_test_check_generate_called_with = []

    def _edi_test_check_generate(self, todo):
        self._edi_test_check_generate_called_with.append(todo)
        return self.env.context.get("_edi_test_check_generate_pass")
