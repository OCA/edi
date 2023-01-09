# Copyright 2022 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "edi.exchange.consumer.mixin"]

    edi_auto_disabled = fields.Boolean(
        states={
            "draft": [("readonly", False)],
            "waiting": [("readonly", False)],
            "confirmed": [("readonly", False)],
            "assigned": [("readonly", False)],
        },
    )

    def _action_done(self):
        res = super()._action_done()
        self._event("on_validate").notify(self)
        return res
