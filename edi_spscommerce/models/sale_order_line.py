# Copyright 2026 Daniel Reis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    x_sps_line_ref = fields.Char(
        "SPS line reference",
        help="Line-level reference sent by the trading partner "
        "(first ReferenceID of the RSX line References block).",
    )
