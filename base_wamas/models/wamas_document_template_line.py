# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class WamasDocumentTemplateLine(models.Model):
    _name = "wamas.document.template.line"
    _description = "WAMAS Document Template Line"

    element_id = fields.Many2one("wamas.document.element", required=True)
    sequence = fields.Integer(required=True, default=10)
    template_id = fields.Many2one("wamas.document.template", "Template")
