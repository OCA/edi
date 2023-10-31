# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class WamasDocumentDefaultField(models.Model):
    _name = "wamas.document.default.field.template"
    _description = "WAMAS Document Default Field Template"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    line_ids = fields.One2many(
        "wamas.document.default.field.template.line",
        "template_id",
        "Lines of Default Fields",
    )
