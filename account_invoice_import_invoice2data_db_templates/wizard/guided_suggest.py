# Copyright 2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Guided-suggest wizard — per-field Keep / Edit / Skip decisions.

Port of the CLI's copier-style ``_interactive_template`` flow into an
Odoo modal wizard. Instead of the CLI's one-field-at-a-time prompt, the
Odoo variant shows every drafted field in a single editable tree so a
non-technical user sees the whole draft at once, ticks Keep on rows that
look right, edits the regex on rows that need tweaking, and Skips rows
that don't belong — then Apply commits only the kept/edited rows to the
template's ``field_ids``.

Rationale: the CLI's one-at-a-time UX helps a developer iterate on a
single field. The Odoo persona (non-regex end user) benefits more from
seeing "these five fields were suggested; which are right?" at a glance,
mirroring how the invoice preview shows the whole extraction on one form.
"""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class GuidedSuggestWizard(models.TransientModel):
    _name = "invoice2data.template.field.walk.wizard"
    _description = "Guided suggest — per-field Keep / Edit / Skip for a template draft"

    template_id = fields.Many2one(
        "invoice2data.template",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    template_name = fields.Char(related="template_id.name", readonly=True)
    line_ids = fields.One2many(
        "invoice2data.template.field.walk.line",
        "wizard_id",
    )
    source = fields.Selection(
        [
            ("deterministic", "Deterministic (find_candidates + labels)"),
            ("ai", "AI (generate_template)"),
        ],
        default="deterministic",
        required=True,
        help=(
            "Which authoring API drafts the field proposals. Deterministic "
            "uses the same helpers as the plain 'Suggest fields' button. "
            "AI requires the [ai] extra + a configured provider."
        ),
    )

    @api.model
    def _from_template(self, template, source="deterministic"):
        """Build a wizard pre-populated with a fresh draft for ``template``."""
        attachment = template._latest_attachment()
        if not attachment:
            raise UserError(
                _(
                    "Attach a sample PDF to the chatter before running "
                    "Guided suggest."
                )
            )
        text = template._extract_text(attachment)
        try:
            if source == "ai":
                from invoice2data.ai.template_generator import generate_template

                draft = generate_template(text)
            else:
                from invoice2data.extract.template_builder import suggested_template

                draft = suggested_template(text)
        except ImportError as exc:
            hint = (
                _(
                    "AI draft requires `pip install 'invoice2data[ai]'` + "
                    "provider env vars. Error: %s"
                )
                if source == "ai"
                else _("invoice2data >= 1.0 required: %s")
            )
            raise UserError(hint % exc) from exc
        existing = {row.name for row in template.field_ids}
        wizard = self.create({"template_id": template.id, "source": source})
        vals = []
        for i, (fname, spec) in enumerate((draft.get("fields") or {}).items()):
            regex, captured = _spec_to_regex_and_preview(spec, text)
            vals.append(
                (
                    0,
                    0,
                    {
                        "sequence": i * 10,
                        "field_name": fname,
                        "proposed_regex": regex,
                        "captured_value": captured or "",
                        "already_in_template": fname in existing,
                        # Skip-by-default rows the template already has;
                        # keep-by-default the fresh ones.
                        "decision": "skip" if fname in existing else "keep",
                    },
                )
            )
        wizard.line_ids = vals
        return wizard

    def action_apply(self):
        """Apply the wizard's kept / edited rows to the template's field grid."""
        self.ensure_one()
        template = self.template_id
        existing = {row.name: row for row in template.field_ids}
        added = replaced = skipped = 0
        for line in self.line_ids:
            if line.decision == "skip":
                skipped += 1
                continue
            regex = line.proposed_regex or ""
            if not regex:
                # A kept row with an empty regex would produce an unusable
                # template field; treat as skip and warn in the log.
                _logger.info(
                    "guided_suggest: skipping %r (kept but empty regex)",
                    line.field_name,
                )
                skipped += 1
                continue
            vals = {"name": line.field_name, "parser": "regex", "regex": regex}
            if line.field_name in existing:
                existing[line.field_name].write(vals)
                replaced += 1
            else:
                template.field_ids = [(0, 0, vals)]
                added += 1
        template.last_test_warnings = _(
            "Guided suggest applied: %(added)d added, %(replaced)d replaced, "
            "%(skipped)d skipped (from %(source)s). Click Test to validate."
        ) % {
            "added": added,
            "replaced": replaced,
            "skipped": skipped,
            "source": self.source,
        }
        return {"type": "ir.actions.act_window_close"}


class GuidedSuggestLine(models.TransientModel):
    _name = "invoice2data.template.field.walk.line"
    _description = "Guided suggest line — one proposed field"
    _order = "sequence, id"

    wizard_id = fields.Many2one(
        "invoice2data.template.field.walk.wizard",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    field_name = fields.Char(readonly=True)
    captured_value = fields.Char(
        readonly=True,
        help=(
            "What the proposed regex captures on the sample text. Empty "
            "means the regex did not match the sample — either edit it or "
            "skip this row."
        ),
    )
    proposed_regex = fields.Char(
        help=(
            "The regex that will be stored on the template field. Editable — "
            "if you tweak it, keep the row selected as 'Keep' and Apply."
        ),
    )
    already_in_template = fields.Boolean(
        readonly=True,
        help=(
            "True when the template already has a field with this name. "
            "Applying with decision=Keep or Edit will REPLACE the existing "
            "regex."
        ),
    )
    decision = fields.Selection(
        [("keep", "Keep"), ("edit", "Edit"), ("skip", "Skip")],
        default="keep",
        required=True,
        help=(
            "Keep = apply the proposed regex as-is. Edit = same as Keep "
            "(so the tweaked regex is used). Skip = don't touch the "
            "template for this field."
        ),
    )


def _spec_to_regex_and_preview(spec, text):
    """Return ``(regex_str, captured_or_none)`` for a template_builder spec.

    ``spec`` may be a bare regex string or a ``{regex, replace}`` dict
    (both shapes are what `suggested_template` returns). Uses
    ``preview_field`` from the same module to compute the captured value
    on ``text``.
    """
    try:
        from invoice2data.extract.template_builder import field_regex, preview_field

        regex = field_regex(spec)
        captured = preview_field(spec, text)
    except Exception as exc:  # noqa: BLE001 -- diagnostic-only
        _logger.debug("guided_suggest: preview failed: %s", exc)
        regex = spec if isinstance(spec, str) else spec.get("regex", "")
        captured = None
    return regex, captured
