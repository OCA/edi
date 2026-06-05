# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    ubl_unece_unit_code = fields.Char(
        readonly=True,
        string="Unece Unit Code",
        help=(
            "Technical field storing the UNECE unit code from UBL import. "
            "Used during purchase reconciliation to identify the corresponding "
            "packaging when a purchase order line is manually selected."
        ),
    )
    ubl_billed_quantity = fields.Float(
        readonly=True,
        help="Technical field storing the billed quantity from the UBL import. "
        "During purchase reconciliation, it allows restoring the original supplier quantity "
        "when the quantity has been altered by packaging selection.",
    )
    ubl_price_unit = fields.Float(
        string="UBL P.U",
        readonly=True,
        help="Technical field storing the unit price from the UBL import.",
    )
