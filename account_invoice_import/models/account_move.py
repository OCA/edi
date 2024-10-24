# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.tools.misc import format_amount


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_move_display_name(self, show_ref=False):
        """Add amount_untaxed in name_get of invoices"""
        name = super()._get_move_display_name(show_ref=show_ref)
        if self.env.context.get("invoice_show_amount"):
            name += _(" Amount w/o tax: %s") % format_amount(
                self.env, self.amount_untaxed, self.currency_id
            )
        return name
