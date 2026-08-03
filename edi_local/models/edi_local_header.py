# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EdiLocalHeader(models.Model):
    _name = "edi.local.header"
    _description = "Edi Local Header"

    sequence = fields.Integer()
    code = fields.Char(required=True)
    name = fields.Char(required=True)

    @api.constrains("code")
    def _check_code(self):
        for local_header in self:
            if self.search_count(
                [
                    ("code", "=", local_header.code),
                    ("id", "!=", local_header.id),
                ],
                limit=1,
            ):
                raise ValidationError(_("The code must be unique."))
