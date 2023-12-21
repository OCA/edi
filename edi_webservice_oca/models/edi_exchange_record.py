# Copyright 2022 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class EDIExchangeRecord(models.Model):
    """
    Define an exchange record.
    """

    _name = "edi.exchange.record"
    _inherit = [
        "edi.exchange.record",
        "webservice.consumer.mixin",
    ]

    def _compute_ws_response_content_filename(self):
        for rec in self:
            rec.ws_response_content_filename = "response_" + rec.exchange_filename
