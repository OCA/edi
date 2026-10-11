# Copyright 2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Click-to-suggest wizard — coord-entry harness for the first slice.

This is the SECOND half of the design brief's click-to-suggest design
(``the internal design brief). The first half —
the server-side pdfium resolution in ``models/pdf_click.py`` — is
feature-complete: given a ``(page, x, y)`` or ``(page, x, y, w, h)``, it
returns a field proposal, its captured value, and a pdftotext cross-
check status.

The remaining piece is the front-end: a wizard that renders the sample
PDF as a page image with a clickable / draggable overlay so the author
doesn't have to type coordinates. That's an OWL widget and lands in a
follow-up PR (its design is stable — see the design brief).

Until the OWL widget arrives, this wizard exposes the server pipeline
as a *coord-entry harness*: enter page + x + y (or drag rect), click
Preview, see the proposal + captured value + cross-check badge. Useful
for validating the pipeline end-to-end today and for regressing it in
tests; the OWL widget will replace only the coord-entry inputs, not
the resolver or the ``Apply`` flow underneath.
"""

import base64
import logging
import tempfile

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PdfClickSuggestWizard(models.TransientModel):
    _name = "invoice2data.template.pdf.click.wizard"
    _description = "Click-to-suggest — pipeline harness (OWL widget in a follow-up)"

    template_id = fields.Many2one(
        "invoice2data.template", required=True, readonly=True, ondelete="cascade"
    )
    template_name = fields.Char(related="template_id.name", readonly=True)

    page = fields.Integer(default=0, help="0-based page index on the sample PDF.")
    x_pt = fields.Float(string="x (pt)", help="Top-left origin, 72 dpi points.")
    y_pt = fields.Float(string="y (pt)", help="Top-left origin, 72 dpi points.")
    w_pt = fields.Float(
        string="width (pt)",
        help="0 = click. Non-zero + non-zero height = drag rectangle → area field.",
    )
    h_pt = fields.Float(string="height (pt)")

    # Populated by Preview.
    proposal_field = fields.Char(readonly=True)
    proposal_value = fields.Char(readonly=True)
    proposal_line = fields.Text(readonly=True)
    proposal_spec = fields.Text(
        readonly=True, help="The regex or {regex, replace} dict to store."
    )
    proposal_note = fields.Text(readonly=True)
    pdftotext_status = fields.Selection(
        [
            ("same", "pdftotext: same value"),
            ("no-match", "pdftotext: no match (backend drift)"),
            ("unavailable", "pdftotext: unavailable"),
        ],
        readonly=True,
    )
    field_key_id = fields.Many2one(
        "invoice2data.field.key",
        string="Canonical field",
        help="Adjust here if the proposal's field is wrong before Apply.",
    )

    def action_preview(self):
        """Resolve the current (page, x, y[, w, h]) to a proposal."""
        self.ensure_one()
        from ..models import pdf_click

        attachment = self.template_id._latest_attachment()
        if not attachment:
            raise UserError(_("Attach a sample PDF to the template's chatter first."))
        with tempfile.NamedTemporaryFile(
            "wb", prefix="i2d-click-", suffix=".pdf", delete=False
        ) as fh:
            fh.write(base64.b64decode(attachment.datas))
            path = fh.name
        try:
            if self.w_pt and self.h_pt:
                result = pdf_click.suggest_area(
                    path, self.page, (self.x_pt, self.y_pt, self.w_pt, self.h_pt)
                )
            else:
                result = pdf_click.suggest_at(path, self.page, self.x_pt, self.y_pt)
        except Exception as exc:  # noqa: BLE001 -- surface via the form
            self.proposal_note = _("Resolver error: %s") % exc
            return self._reopen()
        if "error" in result:
            self.proposal_note = _("No proposal: %s") % result["error"]
            self.proposal_field = ""
            self.proposal_value = ""
            self.proposal_spec = ""
            return self._reopen()
        spec = result.get("spec")
        self.proposal_field = result.get("field") or ""
        self.proposal_value = result.get("value") or ""
        self.proposal_line = result.get("line") or ""
        self.proposal_spec = spec if isinstance(spec, str) else _json_dumps(spec)
        self.proposal_note = result.get("note") or ""
        self.pdftotext_status = result.get("pdftotext_status") or "unavailable"
        # Pre-select the canonical field key if we have one.
        if self.proposal_field:
            key = self.env["invoice2data.field.key"].search(
                [("name", "=", self.proposal_field)], limit=1
            )
            if key:
                self.field_key_id = key.id
        return self._reopen()

    def action_apply(self):
        """Append the previewed proposal as a new field row on the template.

        Also writes ``input_module='pdfium'`` on the template
        (cross-backend-drift guard, per design brief §Q2 recommendation (a)),
        and stores the click hint + sample_value on the new field row so
        Test can regress the capture and the future OWL widget can
        reopen the click position.
        """
        self.ensure_one()
        if not self.proposal_field or not self.proposal_spec:
            raise UserError(_("Nothing to apply — click Preview first."))
        template = self.template_id
        # Pin the backend if not already set. Never OVERWRITE an
        # explicit non-pdfium choice — the author may have set it on
        # purpose.
        if not template.input_module:
            template.input_module = "pdfium"
        # Prefer the canonical-field selection if the user overrode it.
        field_name = (
            self.field_key_id.name if self.field_key_id else self.proposal_field
        )
        # Unpack spec (JSON dict) into regex + replace, or use as-is if bare.
        raw = self.proposal_spec.strip()
        if raw.startswith("{"):
            try:
                spec = _json_loads(raw)
            except Exception:  # noqa: BLE001
                spec = {"regex": raw}
        else:
            spec = {"regex": raw}
        vals = {
            "template_id": template.id,
            "name": field_name,
            "parser": spec.get("parser", "regex"),
            "regex": spec.get("regex", ""),
            "hint_page": self.page,
            "hint_x": self.x_pt,
            "hint_y": self.y_pt,
            "hint_w": self.w_pt,
            "hint_h": self.h_pt,
            "sample_line": (self.proposal_line or "")[:255],
            "sample_value": (self.proposal_value or "")[:255],
        }
        if "replace" in spec and isinstance(spec["replace"], (list, tuple)):
            if len(spec["replace"]) >= 2:
                vals["replace_pattern"] = spec["replace"][0]
                vals["replace_repl"] = spec["replace"][1]
        # If the field already exists on the template, replace it (matches
        # the guided-suggest wizard's Keep-replaces-existing behaviour).
        existing = template.field_ids.filtered(lambda r: r.name == field_name)
        if existing:
            existing[:1].write({k: v for k, v in vals.items() if k != "template_id"})
        else:
            self.env["invoice2data.template.field"].create(vals)
        return {"type": "ir.actions.act_window_close"}

    def _reopen(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @api.model
    def _from_template(self, template):
        wizard = self.create({"template_id": template.id})
        return wizard


def _json_dumps(obj):
    import json

    return json.dumps(obj, indent=2, default=str)


def _json_loads(text):
    import json

    return json.loads(text)
