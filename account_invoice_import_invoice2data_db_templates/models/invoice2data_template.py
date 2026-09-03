# Copyright 2017 Therp BV (foundational DB-storage design)
# Copyright 2025-2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Store invoice2data templates in the database.

The model produces a ``list[InvoiceTemplate]`` that is appended to the
disk-loaded templates by the ``account.invoice.import.invoice2data_parse_invoice``
hook; the lib itself never sees the difference between a disk template and
a DB one.
"""

import base64
import json
import logging
import tempfile

from odoo import _, api, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)

try:
    from invoice2data.extract.invoice_template import InvoiceTemplate
    from invoice2data.extract.loader import ordered_load
    from invoice2data.input.pdftotext import to_text
except ImportError:  # pragma: no cover
    ordered_load = None
    InvoiceTemplate = None
    to_text = None
    logger.debug("invoice2data not importable; install invoice2data >= 1.0")


def _inspect_extraction(templates, text, path):
    """Walk the template pool in priority order and record per-template outcomes.

    Mirrors invoice2data's own dispatch (``prepare_input`` + ``matches_input``
    per template; first successful ``extract`` wins) so we can report which
    templates keyword-matched and, for each, whether ``extract`` succeeded,
    raised (typically :class:`RequiredFieldsMissingError`), or returned falsy.

    Not going through :func:`extract_data` here means the diagnostics are
    deterministic regardless of Odoo's logging config -- earlier versions
    parsed the invoice2data log stream and lost records when a child logger
    had its own level set above DEBUG.

    Returns ``(matched_names, per_template_outcomes, first_full_result)``:

    * ``matched_names`` - set of template_name of every template whose
      keywords matched the (prepared-per-template) text.
    * ``per_template_outcomes`` - list of ``(name, ok, reason_or_none)`` for
      each matched template, ordered by attempt (i.e. priority desc).
    * ``first_full_result`` - the extraction dict of the first template that
      returned truthy, or ``{}`` if none did.
    """
    matched_names = set()
    outcomes = []
    first_full = {}
    ordered = sorted(templates, key=lambda t: -int(t.get("priority", 5) or 5))
    for tpl in ordered:
        name = tpl.get("template_name") or "<unnamed>"
        try:
            optimized = tpl.prepare_input(text)
        except Exception as exc:  # noqa: BLE001 -- surface per-template
            outcomes.append((name, False, "prepare_input error: %s" % exc))
            continue
        if not tpl.matches_input(optimized):
            continue
        matched_names.add(name)
        try:
            extracted = tpl.extract(optimized, invoice_file=path, input_module=None)
        except Exception as exc:  # noqa: BLE001 -- surface per-template
            outcomes.append((name, False, str(exc)))
            continue
        if extracted:
            outcomes.append((name, True, None))
            if not first_full:
                first_full = extracted
        else:
            outcomes.append((name, False, "extract() returned empty"))
    return matched_names, outcomes, first_full


class Invoice2dataTemplate(models.Model):
    """A DB-stored invoice2data template.

    Two authoring modes live side by side:

    * **Power user**: paste / type the full JSON template into ``template``
      and ignore the field editor.
    * **Guided**: name + keywords + per-field rules via the ``field_ids``
      one2many; the JSON is composed from those on read.

    ``get_templates(template_type)`` is the only entry point the import
    wizard needs.
    """

    _name = "invoice2data.template"
    _description = "Template for invoice2data"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, name"

    name = fields.Char(
        required=True,
        copy=False,
        help="Used as the template_name passed to invoice2data.",
    )
    active = fields.Boolean(default=True)
    template_type = fields.Selection(
        selection=[("purchase_invoice", "Purchase Invoice")],
        default="purchase_invoice",
        required=True,
        help=(
            "Filters which DB templates are merged into the invoice2data "
            "run for a given import wizard."
        ),
    )
    priority = fields.Integer(
        default=5,
        help=(
            "Higher-priority templates are tried first, matching the lib's "
            "`priority:` semantics."
        ),
    )
    keywords = fields.Many2many(
        comodel_name="invoice2data.template.keyword",
        relation="invoice2data_template_keyword_rel",
        column1="template_id",
        column2="keyword_id",
        required=True,
        help=(
            "Passed as the template's `keywords:` list. Tags autocomplete "
            "against previously-typed keywords; type-and-enter to create a "
            "new one."
        ),
    )
    exclude_keywords = fields.Many2many(
        comodel_name="invoice2data.template.keyword",
        relation="invoice2data_template_exclude_keyword_rel",
        column1="template_id",
        column2="keyword_id",
        string="Exclude keywords",
        help=(
            "Optional. Passed as the template's `exclude_keywords:` list; "
            "any match here blocks the template even if `keywords` match."
        ),
    )
    template = fields.Text(
        help=(
            "Authoritative JSON for the template (full invoice2data schema). "
            "When empty the JSON is auto-composed from name/keywords/fields."
        ),
    )
    field_ids = fields.One2many(
        comodel_name="invoice2data.template.field",
        inverse_name="template_id",
        copy=True,
    )
    required_fields = fields.Char(
        help=(
            "Comma-separated list of field names invoice2data must extract "
            "for a match to count as successful. Empty = use the library "
            "default ('date, amount, invoice_number, issuer', for invoice "
            "documents). Set to a bare comma to accept ANY extraction "
            "(useful for non-invoice document types such as waybills)."
        ),
    )
    last_test_result = fields.Text(readonly=True)
    last_test_warnings = fields.Text(readonly=True)
    preview_text = fields.Text(readonly=True)

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name)",
            "An invoice2data template with this name already exists.",
        ),
    ]

    # === Public API consumed by the import wizard ===

    @api.model
    def get_templates(self, template_type):
        """Return a list of ``InvoiceTemplate`` objects for the given type.

        Called by the import wizard extension to inject active DB templates
        alongside the disk ones passed to ``invoice2data.extract_data``.
        """
        if InvoiceTemplate is None:
            logger.warning("invoice2data not importable; skipping DB templates")
            return []
        records = self.search(
            [("template_type", "=", template_type), ("active", "=", True)]
        )
        return records._to_invoice_templates()

    # === Authoring helpers ===

    def _compose_template_dict(self):
        """Build the invoice2data template dict from the structured fields."""
        self.ensure_one()
        data = {
            "issuer": self.name,
            "keywords": [kw.name for kw in self.keywords if kw.name],
            "exclude_keywords": [kw.name for kw in self.exclude_keywords if kw.name],
            "priority": self.priority,
            "fields": {},
        }
        if self.required_fields is not None and self.required_fields != "":
            # Split on comma; empty tokens are dropped. A single bare comma
            # yields [] which the lib treats as 'no required fields' -- useful
            # for non-invoice document types (waybills, delivery notes).
            data["required_fields"] = [
                token.strip()
                for token in self.required_fields.split(",")
                if token.strip()
            ]
        for line in self.field_ids:
            data["fields"][line.name] = line._to_field_dict()
        return data

    def _to_invoice_templates(self):
        """Materialise each DB row as an ``InvoiceTemplate`` instance."""
        templates = []
        for record in self:
            try:
                if record.template:
                    candidates = ordered_load(record.template) or []
                else:
                    composed = json.dumps([record._compose_template_dict()])
                    candidates = ordered_load(composed) or []
            except Exception as exc:  # noqa: BLE001 -- never raise during import
                logger.warning(
                    "Failed to load DB invoice2data template %r: %s",
                    record.name,
                    exc,
                )
                continue
            for tpl in candidates:
                tpl["template_name"] = record.name
                templates.append(tpl)
        return templates

    # === Form-view buttons ===

    def action_preview(self):
        """Run the lib's ``to_text`` on the latest chatter attachment."""
        self.ensure_one()
        if to_text is None:
            raise UserError(_("invoice2data is not installed on the server."))
        attachment = self._latest_attachment()
        if not attachment:
            raise UserError(
                _("Attach a sample PDF to the chatter before running Preview.")
            )
        self.preview_text = self._extract_text(attachment)

    _INCLUDE_DISK_PARAM = (
        "account_invoice_import_invoice2data_db_templates.include_disk_templates"
    )

    def action_test(self):
        """Run extract_data() against the disk + DB pool (per system setting)."""
        include_disk = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(self._INCLUDE_DISK_PARAM, default="True")
        )
        return self._run_test(
            include_disk=include_disk.lower() != "false", isolated=False
        )

    def action_test_isolated(self):
        """Run extract_data() against ONLY this template.

        Debug-mode-only button in the header, for template authors iterating
        on a PDF that a disk template (or a sibling DB template) intercepts.
        """
        return self._run_test(include_disk=False, isolated=True)

    def _run_test(self, include_disk, isolated):
        """Shared body for the Test / Test isolated buttons.

        Clears the previous run's output *before* extraction so the form
        never displays stale data when something silently short-circuits.
        Runs per-template inspection so the warnings banner explains WHY a
        given template did or did not produce a result, rather than lumping
        all failure modes into 'invoice2data did not match this PDF'.
        """
        self.ensure_one()
        # Clear stale output up front so a subsequent error / early return
        # can't leave the previous run's success text on screen.
        self.last_test_result = ""
        self.last_test_warnings = ""
        try:
            from invoice2data.extract.loader import read_templates
        except ImportError as exc:
            raise UserError(
                _("invoice2data is not installed on the server: %s") % exc
            ) from exc
        attachment = self._latest_attachment()
        if not attachment:
            raise UserError(
                _("Attach a sample PDF to the chatter before running Test.")
            )
        warnings = []
        try:
            if isolated:
                templates = self._to_invoice_templates()
            else:
                pool = self.search(
                    [
                        ("template_type", "=", self.template_type),
                        ("active", "=", True),
                    ]
                )
                templates = pool._to_invoice_templates()
                if include_disk:
                    templates = read_templates() + templates
            path = self._attachment_to_tempfile(attachment)
            text = to_text(path) if to_text else ""
            matched_names, outcomes, result = _inspect_extraction(templates, text, path)
        except Exception as exc:  # noqa: BLE001 -- surface via the form
            self.last_test_warnings = _("Unhandled error: %s") % exc
            self.last_test_result = ""
            return

        warnings.append(
            _(
                "Templates in pool: %(pool)d | Extracted text: %(chars)d "
                "chars | Isolated: %(iso)s | Include disk: %(disk)s"
            )
            % {
                "pool": len(templates),
                "chars": len(text or ""),
                "iso": _("yes") if isolated else _("no"),
                "disk": _("yes") if (not isolated and include_disk) else _("no"),
            }
        )
        if matched_names:
            names = sorted(matched_names)
            warnings.append(
                _("Templates whose keywords matched: %(n)d (%(names)s)")
                % {
                    "n": len(names),
                    "names": ", ".join(names[:10])
                    + (", ..." if len(names) > 10 else ""),
                }
            )
        else:
            warnings.append(
                _(
                    "No template's keywords matched the extracted text. "
                    "Check your Keywords tags against the Preview text tab; "
                    "invoice2data now treats them as regex (issue #742)."
                )
            )
        # Per-template extract outcome so the author sees each failure verbatim.
        for name, ok, reason in outcomes:
            if ok:
                warnings.append(_("%(name)s: extract OK") % {"name": name})
            else:
                warnings.append(
                    _("%(name)s: %(reason)s") % {"name": name, "reason": reason}
                )
        if not result and matched_names and not outcomes:
            warnings.append(
                _(
                    "Keywords matched but extract() was never attempted "
                    "(unexpected). Check the server log."
                )
            )
        if result:
            matched = result.get("template_name") or ""
            if self.name and matched and matched != self.name:
                warnings.append(
                    _("Winning template is %(matched)r, not %(self)r.")
                    % {"matched": matched, "self": self.name}
                )
            for field in ("amount", "date", "invoice_number", "issuer"):
                if not result.get(field):
                    warnings.append(_("Extracted result missing: %s") % field)
        else:
            warnings.append(
                _(
                    "Tip: to accept a template with no field regexes yet "
                    "(only keywords), set 'Required fields' to a bare comma "
                    "to disable the required-fields check."
                )
            )
        self.last_test_result = json.dumps(result, indent=2, default=str)
        self.last_test_warnings = "\n".join(warnings)
        # Open the extraction preview wizard so the author sees the
        # extraction rendered as an invoice, not just as JSON.
        mode = "isolated" if isolated else ("full" if include_disk else "db_only")
        preview = self.env["invoice2data.template.preview"]._from_extraction(
            self, result or {}, mode, warnings
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Extraction preview: %s") % self.name,
            "res_model": "invoice2data.template.preview",
            "res_id": preview.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_suggest_fields(self):
        """Pre-fill ``field_ids`` from the lib's authoring helpers.

        Uses ``extract.template_builder.suggested_template`` to propose
        regexes for a sample PDF; the user then edits/removes rows.
        """
        self.ensure_one()
        try:
            from invoice2data.extract.template_builder import suggested_template
        except ImportError as exc:
            raise UserError(
                _("invoice2data >= 1.0 is required for Suggest Fields: %s") % exc
            ) from exc
        attachment = self._latest_attachment()
        if not attachment:
            raise UserError(
                _("Attach a sample PDF to the chatter before suggesting fields.")
            )
        text = self._extract_text(attachment)
        draft = suggested_template(text)
        existing = {row.name for row in self.field_ids}
        rows = []
        for fname, spec in (draft.get("fields") or {}).items():
            if fname in existing:
                continue
            row_vals = {"name": fname}
            if isinstance(spec, str):
                row_vals.update({"parser": "regex", "regex": spec})
            elif isinstance(spec, dict):
                row_vals.update(
                    {
                        "parser": spec.get("parser", "regex"),
                        "regex": spec.get("regex", ""),
                    }
                )
                if (
                    isinstance(spec.get("replace"), (list, tuple))
                    and len(spec["replace"]) >= 2
                ):
                    row_vals["replace_pattern"] = spec["replace"][0]
                    row_vals["replace_repl"] = spec["replace"][1]
            rows.append((0, 0, row_vals))
        if rows:
            self.write({"field_ids": rows})

    # === Helpers ===

    def _latest_attachment(self):
        return self.env["ir.attachment"].search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("mimetype", "=", "application/pdf"),
            ],
            order="create_date desc",
            limit=1,
        )

    @staticmethod
    def _attachment_to_tempfile(attachment):
        """Spill an ir.attachment's bytes to a tempfile and return the path."""
        with tempfile.NamedTemporaryFile(
            "wb", prefix="i2d-db-", suffix=".pdf", delete=False
        ) as handle:
            handle.write(base64.b64decode(attachment.datas))
            return handle.name

    @classmethod
    def _extract_text(cls, attachment):
        return to_text(cls._attachment_to_tempfile(attachment))
