# Copyright 2021 Sunflower IT (https://sunflowerweb.nl)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PeppolEasList(models.Model):
    _name = "peppol.eas.list"
    _description = "PEPPOL EAS list"
    _order = "code"

    @api.depends("code", "name")
    def _compute_display_name(self):
        for entry in self:
            entry.display_name = "[{}] {}".format(entry.code, entry.name)

    code = fields.Char(required=True, copy=False)
    name = fields.Char(required=True, copy=False)
    display_name = fields.Char(compute="_compute_display_name", store=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "code_uniq",
            "unique(code)",
            "This EAS code already exists",
        )
    ]

    def name_get(self):
        res = []
        for entry in self:
            res.append((entry.id, "[{}] {}".format(entry.code, entry.name)))
        return res
