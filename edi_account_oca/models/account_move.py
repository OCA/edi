# Copyright 2020 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "edi.exchange.consumer.mixin"]

    edi_disable_auto = fields.Boolean(
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    def _post(self, soft=True):
        result = super()._post(soft=soft)
        # We will use this event to know which documents needs to be executed
        if self:
            self._event("on_post_account_move").notify(self)
        return result

    def button_cancel(self):
        """This could be used to notify our provider that we are not accepting the
        invoice"""
        result = super().button_cancel()
        if self:
            self._event("on_cancel_account_move").notify(self)
        return result

    def _invoice_paid_hook(self):
        """This could be used to notify our provider that we are paying"""
        result = super()._invoice_paid_hook()
        if self:
            self._event("on_paid_account_move").notify(self)
        return result
