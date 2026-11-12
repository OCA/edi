# Copyright 2026 Daniel Reis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class EdiSpsPaymentTermMap(models.Model):
    _name = "edi.sps.payment.term.map"
    _description = "SPS Commerce payment term mapping"
    _rec_name = "payment_term_id"

    net_days = fields.Integer(
        "Net days",
        required=True,
        help="RSX PaymentTerms.TermsNetDueDays value this row maps.",
    )
    payment_term_id = fields.Many2one(
        "account.payment.term",
        required=True,
        ondelete="cascade",
    )

    _sql_constraints = [
        (
            "net_days_uniq",
            "unique(net_days)",
            "Each net-days value can only be mapped once.",
        ),
    ]
