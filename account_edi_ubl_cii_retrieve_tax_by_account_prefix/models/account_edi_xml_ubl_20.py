# Copyright 2026 ACSONE SA/NV,BCIM
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountEdiXmlUbl_20(models.AbstractModel):

    _inherit = "account.edi.xml.ubl_20"

    def _get_tax_by_ubl_values(
        self, journal, amount, tax_unece_code, tax_exemption_reason_code=False, **kwargs
    ):
        taxes = super()._get_tax_by_ubl_values(
            journal,
            amount,
            tax_unece_code,
            tax_exemption_reason_code=tax_exemption_reason_code,
        )
        if (
            "invoice_line" in kwargs
            and kwargs["invoice_line"]
            and kwargs["invoice_line"].account_id
        ):
            allowed_for_account = taxes._filter_allowed_for_account(
                kwargs["invoice_line"].account_id, strict=True
            )
            if allowed_for_account:
                return allowed_for_account
        return taxes
