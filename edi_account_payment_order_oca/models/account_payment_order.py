# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class AccountPaymentOrder(models.Model):
    _name = "account.payment.order"
    _inherit = [_name, "edi.exchange.consumer.mixin"]

    def open2generated(self):
        result = super().open2generated()
        if self:
            self._event("on_action_payment_order_generate_file").notify(self)
        return result
