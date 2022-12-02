# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EDIExchangeType(models.Model):

    _inherit = "edi.exchange.type"

    id_category_ids = fields.Many2many(
        string="ID categories",
        comodel_name="res.partner.id_category",
        help="Allowed ID categories to be used to generate parties information.",
    )
