# Copyright 2020 Creu Blanca
# Copyright 2024 ForgeFlow
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountInvoice(models.Model):
    _name = "account.invoice"
    _inherit = ["account.invoice", "edi.exchange.consumer.mixin"]

    disable_edi_auto = fields.Boolean(
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    def action_invoice_open(self):
        result = super().action_invoice_open()
        # We will use this event to know which documents needs to be executed
        if self:
            self._event("on_open_account_invoice").notify(self)
        return result

    def action_cancel(self):
        """This could be used to notify our provider that we are not accepting the
        invoice"""
        result = super().action_cancel()
        if self:
            self._event("on_cancel_account_invoice").notify(self)
        return result

    def action_invoice_paid(self):
        """This could be used to notify our provider that we are paying"""
        result = super().action_invoice_paid()
        if self:
            self._event("on_paid_account_invoice").notify(self)
        return result
