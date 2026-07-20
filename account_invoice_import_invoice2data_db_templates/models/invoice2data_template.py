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
    keywords = fields.Text(
        required=True,
        help="One keyword per line; passed as the template's `keywords:` list.",
    )
    exclude_keywords = fields.Text(help="Optional; one keyword per line.")
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
        """Return a list of ``InvoiceTemplate`` objects for the given type."""
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
            "keywords": [
                k.strip() for k in (self.keywords or "").splitlines() if k.strip()
            ],
            "exclude_keywords": [
                k.strip()
                for k in (self.exclude_keywords or "").splitlines()
                if k.strip()
            ],
            "priority": self.priority,
            "fields": {},
        }
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

    def action_test(self):
        """Run a full extract_data() against the latest chatter attachment."""
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
            templates = read_templates() + self._to_invoice_templates()
            path = self._attachment_to_tempfile(attachment)
            result = extract_data(path, templates=templates)
        except Exception as exc:  # noqa: BLE001 -- surface via the form
            self.last_test_warnings = str(exc)
            self.last_test_result = ""
            return
        if not result:
            warnings.append(_("invoice2data did not match this PDF."))
        else:
            for field in ("amount", "date", "invoice_number", "issuer"):
                if not result.get(field):
                    warnings.append(_("Required field missing: %s") % field)
        self.last_test_result = json.dumps(result, indent=2, default=str)
        self.last_test_warnings = "\n".join(warnings) if warnings else ""

    def action_suggest_fields(self):
        """Pre-fill ``field_ids`` from the lib's authoring helpers."""
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
        draft = suggested_template(text, name=self.name or "draft")
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
