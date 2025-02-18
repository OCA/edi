# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models

from ..utils import normalize_string


class EDIBackendType(models.Model):
    """Define a kind of backend."""

    _name = "edi.backend.type"
    _description = "EDI Backend Type"

    name = fields.Char(required=True)
    code = fields.Char(
        required=True,
        inverse="_inverse_code",
    )

    _sql_constraints = [
        ("uniq_code", "unique(code)", "Backend type code must be unique!")
    ]

    @api.onchange("name", "code")
    def _onchange_code(self):
        for rec in self:
            rec.code = rec.code or rec.name

    def _inverse_code(self):
        for rec in self:
            # Make sure it's always normalized
            rec.code = normalize_string(rec.code)
