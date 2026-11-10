# Copyright 2026 Gray Matter Logic
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "edi.exchange.consumer.mixin"]
