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
    code = fields.Char(required=True)

    _sql_constraints = [
        ("uniq_code", "unique(code)", "Backend type code must be unique!")
    ]

    @api.onchange("name", "code")
    def _onchange_code(self):
        self.code = self.code or self.name

    @api.model
    def create(self, vals):
        result = super(EDIBackendType, self).create(vals)
        if result.code:
            result.code = normalize_string(result.code)
        return result

    @api.multi
    def write(self, vals):
        if "code" in vals:
            code = normalize_string(vals.get("code"))
            vals.update({"code": code})
        return super(EDIBackendType, self).write(vals)
