# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("amount_untaxed", "currency_id")
    def _compute_display_name(self):
        """Add amount_untaxed in name_get of sale orders"""
        res = super()._compute_display_name()
        if self._context.get("sale_order_show_amount"):
            for order in self:
                # TODO: find a python method to easily display a float + currency
                # symbol (before or after) depending on lang of context and currency
                name = _(
                    "%(so_name)s Amount w/o tax: %(amount)s %(currency)s",
                    so_name=order.name,
                    amount=order.amount_untaxed,
                    currency=order.currency_id.name,
                )
                order.display_name = name
        return res
