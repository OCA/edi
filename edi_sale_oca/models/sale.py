# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "edi.exchange.consumer.mixin"]

    def action_confirm(self):
        result = super().action_confirm()
        if self:
            self._event("on_action_confirm_sale_order").notify(self)
        return result

    def action_cancel(self):
        result = super().action_cancel()
        if self:
            self._event("on_action_cancel_sale_order").notify(self)
        return result
