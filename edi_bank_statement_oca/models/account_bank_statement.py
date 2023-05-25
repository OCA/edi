# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class AccountBankStatement(models.Model):
    _name = "account.bank.statement"
    _inherit = ["account.bank.statement", "edi.exchange.consumer.mixin"]

    def action_bank_reconcile_bank_statements(self):
        result = super().action_bank_reconcile_bank_statements()
        if self:
            self._event("on_action_bank_reconcile_bank_statements").notify(self)
        return result
