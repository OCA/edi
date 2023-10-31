# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class WamasDocumentDefaultFieldLine(models.Model):
    _name = "wamas.document.default.field.template.line"
    _description = "WAMAS Document Default Field Template Line"
    _rec_name = "df_field_id"

    df_field_id = fields.Many2one(
        "wamas.document.default.field", "Default Field", required=True
    )
    sequence = fields.Integer(required=True, default=10)
    template_id = fields.Many2one("wamas.document.default.field.template", "Template")
