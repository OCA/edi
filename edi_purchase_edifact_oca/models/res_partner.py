# Copyright 2024 Trobz
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    edifact_purchase_order_out = fields.Boolean(
        string="Export Purchase Order with EDIFACT",
        default=False
    )
