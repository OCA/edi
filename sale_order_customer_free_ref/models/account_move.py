# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    customer_order_number = fields.Char(string="Customer Order Number", copy=False)
    customer_order_free_ref = fields.Char(string="Customer Free Reference", copy=False)
