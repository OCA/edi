# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResParter(models.Model):
    _inherit = "res.partner"

    ediversa_id = fields.Char()
