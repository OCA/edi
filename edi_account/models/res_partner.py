# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    account_move_edi_format_ids = fields.Many2many(
        "edi.format", domain=[("res_model", "=", "account.move")]
    )
