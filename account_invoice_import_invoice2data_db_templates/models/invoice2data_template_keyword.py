# Copyright 2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""A reusable keyword (or exclude-keyword) atom for DB-stored templates.

Templates share a common pool of keyword records so the ``many2many_tags``
widget in the template form can autocomplete against previously-typed
keywords and (with the ``ir.attachment`` autocomplete) surface reuse across
templates.
"""

from odoo import fields, models


class Invoice2dataTemplateKeyword(models.Model):
    _name = "invoice2data.template.keyword"
    _description = "Keyword atom used by invoice2data DB templates"
    _order = "name"
    _rec_name = "name"

    name = fields.Char(
        required=True,
        help=(
            "The raw string invoice2data uses to match against the extracted "
            "text. May be a plain substring or a regex (see issue #742 in the "
            "upstream library — keywords are regex-matched with a literal "
            "fallback)."
        ),
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name)",
            "This keyword already exists; reuse the existing entry rather "
            "than creating a duplicate.",
        ),
    ]
