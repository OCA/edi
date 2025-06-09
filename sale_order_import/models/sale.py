# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends_context("sale_order_show_amount")
    def _compute_display_name(self):
        if not self.env.context.get("sale_order_show_amount"):
            return super()._compute_display_name()
        for order in self:
            # TODO: find a python method to easily display a float + currency
            # symbol (before or after) depending on lang of context and currency
            order.display_name = order.name + self.env._(
                " Amount w/o tax: %(amount)s %(currency)s",
                amount=order.amount_untaxed,
                currency=order.currency_id.name,
            )
