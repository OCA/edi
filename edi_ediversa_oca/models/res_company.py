# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    use_edi_ediversa = fields.Boolean()
    edi_ediversa_test = fields.Boolean(string="EDI Ediversa Test Environment")
    edi_ediversa_user = fields.Char()
    edi_ediversa_password = fields.Char()
