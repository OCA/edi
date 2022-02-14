# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "edi.exchange.consumer.mixin"]

    def button_confirm(self):
        result = super().button_confirm()
        if self:
            self._event("on_button_confirm_purchase_order").notify(self)
        return result

    def button_cancel(self):
        result = super().button_cancel()
        if self:
            self._event("on_button_cancel_purchase_order").notify(self)
        return result
