# Copyright 2025-2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Per-field extraction rule for a DB-stored invoice2data template.

Selection lists are driven from the lib's canonical schema
(``invoice2data.extract.schema``) so adding a new canonical field there
automatically becomes selectable here -- no parallel maintenance.
"""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)


def _field_selection(self):
    """Best-effort selection list from the lib's canonical schema.

    Odoo invokes selection callables with ``self`` bound, so the parameter
    is required even though we do not use it -- adding it stops the
    ``TypeError: _field_selection() takes 0 positional arguments but 1 was
    given`` raised at load time.
    """
    try:
        from invoice2data.extract import schema
    except ImportError:
        return [("invoice_number", "Invoice Number"), ("date", "Date")]
    return [
        (name, name.replace("_", " ").title()) for name in sorted(schema.INVOICE_FIELDS)
    ]


class Invoice2dataTemplateField(models.Model):
    _name = "invoice2data.template.field"
    _description = "Per-field extraction rule for a DB-stored invoice2data template"
    _order = "sequence, id"

    template_id = fields.Many2one(
        comodel_name="invoice2data.template",
        ondelete="cascade",
        required=True,
        index=True,
    )
    sequence = fields.Integer(default=10)
    name = fields.Selection(
        selection=_field_selection,
        required=True,
        help="Canonical invoice2data field name (from `extract/schema.py`).",
    )
    parser = fields.Selection(
        selection=[
            ("regex", "Regex"),
            ("static", "Static value"),
            ("lines", "Lines block (advanced)"),
        ],
        default="regex",
        required=True,
    )
    regex = fields.Char(
        help="Capture-group regex; used when parser is 'regex' or 'lines'.",
    )
    static_value = fields.Char(
        help="Constant value emitted as-is; used when parser is 'static'.",
    )
    type = fields.Selection(
        selection=[
            ("char", "Text"),
            ("int", "Integer"),
            ("float", "Float"),
            ("date", "Date"),
        ],
        default="char",
    )
    # Per-field `replace` (issue invoice2data#497): a (pattern, repl) pair the
    # lib applies to the captured value before coercion. Kept as two strings
    # rather than a JSON pair so non-Python authors don't need to escape.
    replace_pattern = fields.Char(string="Replace pattern")
    replace_repl = fields.Char(string="Replace with")
    # Issue invoice2data#652: extracts the first numeric token from a
    # captured value before type coercion.
    extract_number = fields.Boolean(
        help=(
            "Pluck the first numeric token from the captured value before "
            "type coercion. Useful for `12123 Stk.` -> `12123`. Only honoured "
            "when type is Integer or Float."
        ),
    )

    # Click-to-suggest bookkeeping (design brief Q4): Odoo-only, does NOT
    # export into the YAML template. Lets the wizard reopen the click
    # position later ("show me where") and lets Test assert that the
    # captured value on the current sample still matches the value seen
    # when the rule was authored.
    hint_page = fields.Integer(
        string="Hint page",
        help=(
            "0-based page index of the click / drag on the sample PDF. "
            "Together with x/y (and w/h for a drag) it lets the builder "
            "reopen the exact position later."
        ),
    )
    hint_x = fields.Float(string="Hint x (pt)")
    hint_y = fields.Float(string="Hint y (pt)")
    hint_w = fields.Float(
        string="Hint w (pt)",
        help="Drag-rectangle width in points; zero for click-only rules.",
    )
    hint_h = fields.Float(string="Hint h (pt)")
    sample_line = fields.Char(
        help=(
            "The bbox line text the click landed on. Kept for repro "
            "('open the click position again') and for a fuzzy re-anchor "
            "when the regex fails to re-match after a small layout change."
        ),
    )
    sample_value = fields.Char(
        help=(
            "What this rule's regex captured on the sample PDF at authoring "
            "time. The Test button flags a regression if the current "
            "extraction returns a different value."
        ),
    )

    @api.constrains("parser", "regex", "static_value")
    def _check_parser_args(self):
        for line in self:
            if line.parser in {"regex", "lines"} and not line.regex:
                raise ValidationError(
                    _(
                        "Field '%(field)s' uses parser '%(parser)s' but has "
                        "no regex set."
                    )
                    % {"field": line.name, "parser": line.parser}
                )
            if line.parser == "static" and not line.static_value:
                raise ValidationError(
                    _("Field '%(field)s' uses parser 'static' but has no " "value set.")
                    % {"field": line.name}
                )

    def _to_field_dict(self):
        """Render this row as the dict the invoice2data template expects."""
        self.ensure_one()
        if self.parser == "static":
            return {"parser": "static", "value": self.static_value or ""}
        spec = {"parser": self.parser, "regex": self.regex or ""}
        if self.type and self.type != "char":
            spec["type"] = self.type
        if self.replace_pattern:
            spec["replace"] = [self.replace_pattern, self.replace_repl or ""]
        if self.extract_number and self.type in {"int", "float"}:
            spec["extract_number"] = True
        return spec
