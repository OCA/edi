# Copyright 2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Wizard to import bundled/disk-loaded invoice2data templates into the DB.

Copies YAML/JSON templates shipped by the invoice2data library (or by the
sysadmin's ``INVOICE2DATA_TEMPLATES_DIR``) into ``invoice2data.template``
records, giving the author a starting point they can then customise via
the field editor / JSON tab / keywords tags.

The disk template dict is serialised into the record's ``template`` JSON
field verbatim (so nothing about the source template is lost — including
options, lines blocks, and any keys the field editor does not surface).
Keywords / exclude_keywords are ALSO populated as m2m tags so they show
up in the header of the imported record.
"""

import json
import logging
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Invoice2dataTemplateImportDiskWizard(models.TransientModel):
    _name = "invoice2data.template.import.disk.wizard"
    _description = "Import bundled invoice2data templates into the DB"

    name_regex = fields.Char(
        string="Filter template name (regex)",
        help=(
            "Only templates whose filename matches this Python regex are "
            "imported. Leave blank to import ALL bundled templates "
            "(currently ~215). Example: '^nl\\.' to import only Dutch "
            "vendors, 'shell' to import both nl.shell.* and be.shell.*."
        ),
    )
    mode = fields.Selection(
        selection=[
            ("skip_existing", "Skip if name already exists"),
            ("overwrite", "Overwrite existing records"),
        ],
        default="skip_existing",
        required=True,
    )
    dry_run = fields.Boolean(
        default=False,
        help=(
            "Report how many templates WOULD be imported without creating or "
            "modifying any records."
        ),
    )
    result_summary = fields.Text(readonly=True)

    def action_import(self):
        """Read disk templates, filter, create/update DB records.

        Returns a client action re-opening the wizard so the user can see
        ``result_summary`` populated with counts.
        """
        self.ensure_one()
        try:
            from invoice2data.extract.loader import read_templates
        except ImportError as exc:
            raise UserError(
                _("invoice2data is not importable on the server: %s") % exc
            ) from exc

        try:
            pattern = re.compile(self.name_regex) if self.name_regex else None
        except re.error as exc:
            raise UserError(
                _("Invalid regex %(rx)r: %(err)s") % {"rx": self.name_regex, "err": exc}
            ) from exc

        disk_templates = read_templates()
        Template = self.env["invoice2data.template"]
        Keyword = self.env["invoice2data.template.keyword"]
        keyword_cache = {}

        considered = created = updated = skipped = 0
        errors = []

        for disk_tpl in disk_templates:
            name = disk_tpl.get("template_name", "")
            if pattern and not pattern.search(name):
                continue
            considered += 1
            existing = Template.search([("name", "=", name)], limit=1)
            if existing and self.mode == "skip_existing":
                skipped += 1
                continue
            if self.dry_run:
                if existing:
                    updated += 1
                else:
                    created += 1
                continue

            try:
                vals = self._vals_from_disk_template(disk_tpl, Keyword, keyword_cache)
            except Exception as exc:  # noqa: BLE001 -- report per-template
                errors.append("%s: %s" % (name, exc))
                _logger.warning(
                    "import_disk_templates: failed to import %r: %s", name, exc
                )
                continue

            if existing:
                existing.write(vals)
                updated += 1
            else:
                Template.create(vals)
                created += 1

        summary_lines = [
            _("Considered: %d") % considered,
            _("Created:    %d") % created,
            _("Updated:    %d") % updated,
            _("Skipped:    %d (already existed)") % skipped,
        ]
        if errors:
            summary_lines.append("")
            summary_lines.append(_("Errors (%d):") % len(errors))
            summary_lines.extend(errors[:20])
            if len(errors) > 20:
                summary_lines.append(
                    _("... %d more suppressed; check server log") % (len(errors) - 20)
                )
        if self.dry_run:
            summary_lines.insert(0, _("[DRY RUN — no records touched]"))
        self.result_summary = "\n".join(summary_lines)
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @staticmethod
    def _clean_template_dict(disk_tpl):
        """Strip runtime-only keys before serialising the disk template."""
        out = dict(disk_tpl)  # InvoiceTemplate is a dict subclass
        # `template_name` lives on the DB record's `name` field; strip it
        # from the JSON blob so a rename works.
        out.pop("template_name", None)
        return out

    @api.model
    def _vals_from_disk_template(self, disk_tpl, Keyword, keyword_cache):
        """Turn one on-disk InvoiceTemplate into create/write values."""
        name = disk_tpl.get("template_name", "")
        if not name:
            raise ValueError("template has no template_name; cannot import")
        keyword_ids = self._ensure_keyword_ids(
            disk_tpl.get("keywords") or [], Keyword, keyword_cache
        )
        exclude_keyword_ids = self._ensure_keyword_ids(
            disk_tpl.get("exclude_keywords") or [], Keyword, keyword_cache
        )
        return {
            "name": name,
            "priority": int(disk_tpl.get("priority") or 5),
            "keywords": [(6, 0, keyword_ids)],
            "exclude_keywords": [(6, 0, exclude_keyword_ids)],
            "template": json.dumps(
                self._clean_template_dict(disk_tpl), indent=2, default=str
            ),
            "active": True,
        }

    @staticmethod
    def _ensure_keyword_ids(names, Keyword, cache):
        """Return ids of keyword records for each name, creating on miss."""
        ids = []
        for raw in names:
            name = raw if isinstance(raw, str) else str(raw)
            name = name.strip()
            if not name:
                continue
            if name in cache:
                ids.append(cache[name])
                continue
            existing = Keyword.search([("name", "=", name)], limit=1)
            if existing:
                cache[name] = existing.id
            else:
                cache[name] = Keyword.create({"name": name}).id
            ids.append(cache[name])
        return ids
