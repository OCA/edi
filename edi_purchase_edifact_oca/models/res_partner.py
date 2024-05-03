# Copyright 2024 Trobz
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    edifact_purchase_order_out = fields.Boolean(
        string="Export Purchase Order with EDIFACT",
        default=False
    )

    edifact_despatch_advice_ignore_lines_with_unknown_products = fields.Boolean(
        default=True,
        help="""When this option is enabled,
            we will ignore lines with unknown products
            when processing a Despatch Advice of this supplier.
        """,
    )
