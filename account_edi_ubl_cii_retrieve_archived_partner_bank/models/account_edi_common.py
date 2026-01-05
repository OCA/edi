# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountEdiCommon(models.AbstractModel):

    _inherit = "account.edi.common"

    def _import_retrieve_and_fill_partner_bank_details(self, invoice, bank_details):
        # disable active_test to allow retrieving archived partner bank accounts
        # for safety reasons, when a bank account is reactivated, allow_out_payment is
        # set to False
        res = super(
            AccountEdiCommon, self.with_context(active_test=False)
        )._import_retrieve_and_fill_partner_bank_details(invoice, bank_details)
        bank_account = invoice.partner_bank_id
        if bank_account and not bank_account.active:
            bank_account.write({"active": True, "allow_out_payment": False})
        return res
