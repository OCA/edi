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


class _CapturingHandler(logging.Handler):
    """Collect log records for later inspection by ``_diagnose_captured``."""

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)


def _diagnose_captured(handler):
    """Extract (matched_template_names, incomplete_reasons) from captured logs.

    invoice2data emits well-known message shapes we can cheaply parse:

    * ``Template: X | Keywords matched.`` - one per template whose keywords
      passed. Set of names surfaced so the author sees which templates the
      library considered before choosing (or failing).
    * ``Template X matched under Y but extraction was incomplete: <reason>``
      - each partial-extraction reason, most useful when the author's own
      template matched keywords but its regexes didn't fill required fields.
    """
    matched = set()
    incomplete = []
    for record in handler.records:
        msg = record.getMessage()
        if "| Keywords matched" in msg:
            # 'Template: <name> | Keywords matched. No exclude keywords found.'
            head = msg.split("|", 1)[0]
            name = head.replace("Template:", "").strip()
            if name:
                matched.add(name)
        elif "extraction was incomplete" in msg:
            # 'Template X matched under Y but extraction was incomplete: ...'
            _, _, reason = msg.partition("extraction was incomplete:")
            reason = reason.strip() or msg
            incomplete.append(reason)
    return matched, incomplete


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
        self._run_test(include_disk=include_disk.lower() != "false", isolated=False)

    def action_test_isolated(self):
        """Run extract_data() against ONLY this template.

        Debug-mode-only button in the header, for template authors iterating
        on a PDF that a disk template (or a sibling DB template) intercepts.
        """
        self._run_test(include_disk=False, isolated=True)

    def _run_test(self, include_disk, isolated):
        """Shared body for the Test / Test isolated buttons.

        Distinguishes three outcomes the invoice2data library conflates into
        an empty ``extract_data`` return:

        * No keyword-match: no template's keywords survived on this PDF's
          extracted text.
        * Keyword-match but incomplete extraction: at least one template
          matched keywords, but its field grid did not fill the required
          fields (defaults to date/amount/invoice_number/issuer, or the
          template's own ``required_fields`` override).
        * Successful extraction: emitted as normal.

        The diagnosis comes from capturing invoice2data's own log records
        during the ``extract_data`` call, then parsing them for well-known
        message shapes. Without this the author sees only "no match" and
        cannot tell whether it's their keywords, their regexes, or a
        different template that intercepted the PDF.
        """
        self.ensure_one()
        try:
            from invoice2data import extract_data
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
            text = self._extract_text(attachment)
            path = self._attachment_to_tempfile(attachment)
            captured = _CapturingHandler()
            i2d_root = logging.getLogger("invoice2data")
            i2d_root.addHandler(captured)
            prior_level = i2d_root.level
            i2d_root.setLevel(logging.DEBUG)
            try:
                result = extract_data(path, templates=templates)
            finally:
                i2d_root.removeHandler(captured)
                i2d_root.setLevel(prior_level)
        except Exception as exc:  # noqa: BLE001 -- surface via the form
            self.last_test_warnings = str(exc)
            self.last_test_result = ""
            return

        # Header: cheap facts the author always wants.
        warnings.append(
            _("Templates in pool: %(pool)d | Extracted text: %(chars)d chars")
            % {"pool": len(templates), "chars": len(text or "")}
        )
        matched_names, incomplete_reasons = _diagnose_captured(captured)
        if matched_names:
            warnings.append(
                _("Templates whose keywords matched: %(n)d (%(names)s)")
                % {
                    "n": len(matched_names),
                    "names": ", ".join(sorted(matched_names)[:10])
                    + (", ..." if len(matched_names) > 10 else ""),
                }
            )
        else:
            warnings.append(
                _(
                    "No template's keywords matched the extracted text. Check "
                    "your Keywords tags against the Preview text tab."
                )
            )

        if not result:
            # Keyword match but no complete extraction anywhere.
            if incomplete_reasons:
                for line in incomplete_reasons:
                    warnings.append(_("Incomplete extraction: %s") % line)
                warnings.append(
                    _(
                        "No template completed extraction. Add regexes to the "
                        "Fields tab (or paste JSON) so the required fields "
                        "come out. For non-invoice documents, set "
                        "'Required fields' to a bare comma to disable the "
                        "check entirely."
                    )
                )
        else:
            matched = result.get("template_name") or ""
            if self.name and matched and matched != self.name:
                warnings.append(
                    _(
                        "These results come from template %(matched)r, not "
                        "%(self)r. Your template did not complete extraction; "
                        "the shown fields are what the winning template "
                        "extracted."
                    )
                    % {"matched": matched, "self": self.name}
                )
            for field in ("amount", "date", "invoice_number", "issuer"):
                if not result.get(field):
                    warnings.append(_("Extracted result missing: %s") % field)
        self.last_test_result = json.dumps(result, indent=2, default=str)
        self.last_test_warnings = "\n".join(warnings) if warnings else ""

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
