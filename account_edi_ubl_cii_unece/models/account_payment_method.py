# Copyright 2026 Akretion France (https://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    unece_code = fields.Selection(
        # Codes from UNTDID 4461
        # https://service.unece.org/trade/untdid/d24a/tred/tred4461.htm
        # The list is long: we selected codes that are used "in real life"
        # Don't hesitate to propose a PR to add codes that are used
        # in real life by real companies
        [
            ("10", "10 - Cash"),
            ("20", "20 - Cheque"),
            ("24", "24 - Bill of exchange awaiting acceptance"),
            ("30", "30 - Credit transfer"),
            ("44", "44 - Accepted bill of exchange"),
            ("48", "48 - Bank card"),
            ("49", "49 - Direct debit"),
            ("58", "58 - SEPA credit transfer"),
            ("59", "59 - SEPA direct debit"),
            ("60", "60 - Promissory note"),
            ("61", "61 - Promissory note signed by the debtor"),
            ("70", "70 - Bill drawn by the creditor on the debtor"),
            ("97", "97 - Clearing between partners"),
        ],
        string="UNECE Payment Mean",
        compute="_compute_unece_code",
        store=True,
        readonly=False,
    )

    @api.depends("code")
    def _compute_unece_code(self):
        code2unece = {
            "manual": "30",
            "sepa_credit_transfer": "58",
            "sepa_direct_debit": "59",
            "fr_lcr": "70",
        }
        for method in self:
            method.unece_code = code2unece.get(method.code)
