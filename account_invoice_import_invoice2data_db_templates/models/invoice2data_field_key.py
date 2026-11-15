# Copyright 2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Allow-list of canonical fields the click-to-suggest picker offers.

Per the design brief (Q3): the wizard's field-select dropdown is sourced
from Odoo at runtime, not from ``invoice2data.extract.schema``, so that
l10n glue modules can add locale-specific rows (SIREN, OIN, KvK, ...)
without a library change. Each row names a canonical invoice2data field
key plus optionally a hint ``ir.model.fields`` on ``account.move`` /
``res.partner`` for downstream reference.
"""

from odoo import fields, models


class Invoice2dataFieldKey(models.Model):
    _name = "invoice2data.field.key"
    _description = "Allow-list of canonical invoice2data field keys"
    _order = "sequence, name"

    name = fields.Char(
        required=True,
        help=(
            "The invoice2data canonical field name — matches what appears "
            "in a YAML template's `fields:` mapping (e.g. `amount`, `date`, "
            "`invoice_number`, `vat`, `partner_name`)."
        ),
    )
    label = fields.Char(
        help="Human label shown in the picker; falls back to `name`.",
    )
    sequence = fields.Integer(default=10)
    kind = fields.Selection(
        [
            ("header", "Invoice header"),
            ("partner", "Partner / vendor"),
            ("amount", "Amount / tax"),
            ("line", "Line item"),
            ("identifier", "Identifier (VAT / IBAN / BIC)"),
            ("other", "Other"),
        ],
        default="other",
    )
    field_ref = fields.Many2one(
        "ir.model.fields",
        string="Odoo field",
        help=(
            "Optional pointer to the underlying `ir.model.fields` on "
            "`account.move` / `res.partner`. Purely informational — the "
            "invoice2data template uses the canonical name, not this ref."
        ),
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name)",
            "A field key with this name already exists.",
        ),
    ]
