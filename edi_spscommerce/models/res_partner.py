# Copyright 2026 Daniel Reis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = ["res.partner"]

    x_sps_location = fields.Char(
        "SPS location ID",
        help="SPS/GLN location identifier for this address "
        "(RSX AddressLocationNumber). Used to match ship-to addresses "
        "on inbound orders.",
    )
    x_sps_trading_partner_id = fields.Char(
        "SPS trading partner ID",
        help="The customer's SPS Commerce trading partner id, sent as "
        "RSX TradingPartnerId on outbound documents and matched on "
        "inbound orders. Falls back to Internal Reference when empty.",
    )
