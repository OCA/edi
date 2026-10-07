# Copyright 2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Preview an invoice2data extraction as it would look on the target Odoo model.

Renders the fields invoice2data would fill on the target document
(currently account.move for purchase_invoice templates) in an
invoice-shaped read-only form: partner block + invoice header + line
items + totals footer. Non-technical template authors read this instead
of the raw JSON blob to answer "does the extraction look right?".

The wizard is a TransientModel — no records persist. The Test / Test
isolated buttons run extract_data as before (populating the template
record's last_test_result / last_test_warnings for the diagnostics
banner) and return an act_window that opens this wizard in a modal.
"""

import logging
from datetime import date, datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Invoice2dataTemplatePreview(models.TransientModel):
    _name = "invoice2data.template.preview"
    _description = "Invoice2data extraction preview"

    template_id = fields.Many2one(
        "invoice2data.template",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    template_name = fields.Char(related="template_id.name", readonly=True)
    winning_template_name = fields.Char(
        readonly=True,
        help=(
            "The template invoice2data actually picked — may differ from "
            "the one being authored when a sibling / disk template wins."
        ),
    )
    mode = fields.Selection(
        [("isolated", "Isolated"), ("db_only", "DB only"), ("full", "Disk + DB")],
        readonly=True,
    )

    # --- Partner block (mirrors res.partner shape) --------------------
    partner_name = fields.Char(readonly=True)
    partner_vat = fields.Char(string="VAT", readonly=True)
    partner_email = fields.Char(readonly=True)
    partner_street = fields.Char(readonly=True)
    partner_zip = fields.Char(string="ZIP", readonly=True)
    partner_city = fields.Char(readonly=True)
    partner_country_code = fields.Char(string="Country", readonly=True)
    partner_id = fields.Many2one(
        "res.partner",
        string="Matched partner",
        readonly=True,
        help=(
            "Best partner match found in Odoo. Tries VAT first, then a "
            "case-insensitive name search. Empty means the import would "
            "either create a new partner or reject the invoice depending "
            "on the import wizard configuration."
        ),
    )

    # --- Invoice header (mirrors account.move shape) ------------------
    invoice_ref = fields.Char(string="Vendor invoice / reference", readonly=True)
    invoice_date = fields.Date(readonly=True)
    invoice_date_due = fields.Date(string="Due date", readonly=True)
    payment_reference = fields.Char(readonly=True)
    currency_id = fields.Many2one("res.currency", readonly=True)

    # --- Amount footer -----------------------------------------------
    amount_untaxed = fields.Monetary(currency_field="currency_id", readonly=True)
    amount_tax = fields.Monetary(currency_field="currency_id", readonly=True)
    amount_total = fields.Monetary(currency_field="currency_id", readonly=True)

    # --- Lines --------------------------------------------------------
    line_ids = fields.One2many(
        "invoice2data.template.preview.line",
        "preview_id",
        readonly=True,
    )
    tax_line_ids = fields.One2many(
        "invoice2data.template.preview.tax", "preview_id", readonly=True
    )

    # --- Diagnostics --------------------------------------------------
    missing_fields = fields.Char(
        readonly=True,
        help=(
            "Canonical field names that the invoice-import wizard would "
            "typically want but this extraction did not yield. Empty = "
            "nothing missing."
        ),
    )
    warnings = fields.Text(readonly=True)
    raw_json = fields.Text(readonly=True)

    # --- Constructor ---------------------------------------------------

    @api.model
    def _from_extraction(self, template, extracted, mode, warnings):
        """Build a preview record from an invoice2data extraction dict.

        Args:
            template (invoice2data.template): the template being tested.
            extracted (dict): what extract_data returned (may be empty).
            mode (str): 'isolated' / 'db_only' / 'full'.
            warnings (list[str]): the diagnostic lines from _run_test.
        """
        vals = {
            "template_id": template.id,
            "mode": mode,
            "warnings": "\n".join(warnings) if warnings else "",
            "raw_json": _dumps(extracted) if extracted else "",
        }
        if extracted:
            vals["winning_template_name"] = extracted.get("template_name") or ""
            vals.update(self._extract_partner_vals(self.env, extracted))
            vals.update(self._extract_header_vals(self.env, extracted))
            vals.update(self._extract_amount_vals(extracted))
            vals["missing_fields"] = ", ".join(self._missing(extracted)) or ""
        preview = self.create(vals)
        preview.line_ids = [
            (0, 0, spec) for spec in self._line_vals(extracted.get("lines") or [])
        ]
        preview.tax_line_ids = [
            (0, 0, spec)
            for spec in self._tax_line_vals(extracted.get("tax_lines") or [])
        ]
        return preview

    # --- Field extractors --------------------------------------------

    @staticmethod
    def _extract_partner_vals(env, extracted):
        vals = {
            "partner_name": extracted.get("partner_name") or extracted.get("issuer"),
            "partner_vat": extracted.get("vat"),
            "partner_email": extracted.get("partner_email"),
            "partner_street": extracted.get("partner_street"),
            "partner_zip": extracted.get("partner_zip"),
            "partner_city": extracted.get("partner_city"),
            "partner_country_code": extracted.get("country_code"),
        }
        # Best-effort partner match — VAT first (exact, case-insensitive
        # after stripping spaces), name fallback (case-insensitive
        # substring). Skips silently on any lookup error so a broken
        # search filter can't kill the preview.
        Partner = env["res.partner"].sudo()
        try:
            partner = env["res.partner"].browse()
            if vals["partner_vat"]:
                clean = vals["partner_vat"].replace(" ", "").upper()
                partner = Partner.search([("vat", "=ilike", clean)], limit=1)
            if not partner and vals["partner_name"]:
                partner = Partner.search(
                    [("name", "=ilike", vals["partner_name"])], limit=1
                )
            vals["partner_id"] = partner.id if partner else False
        except Exception as exc:  # noqa: BLE001 -- diagnostic-only
            _logger.debug("preview: partner lookup failed: %s", exc)
        return vals

    @staticmethod
    def _extract_header_vals(env, extracted):
        vals = {
            "invoice_ref": extracted.get("invoice_number"),
            "invoice_date": _to_date(extracted.get("date")),
            "invoice_date_due": _to_date(extracted.get("date_due")),
            "payment_reference": extracted.get("payment_reference"),
        }
        code = extracted.get("currency")
        if code:
            currency = (
                env["res.currency"]
                .with_context(active_test=False)
                .search([("name", "=", code)], limit=1)
            )
            vals["currency_id"] = currency.id if currency else False
        return vals

    @staticmethod
    def _extract_amount_vals(extracted):
        return {
            "amount_total": extracted.get("amount") or 0.0,
            "amount_untaxed": extracted.get("amount_untaxed") or 0.0,
            "amount_tax": extracted.get("amount_tax") or 0.0,
        }

    @staticmethod
    def _missing(extracted):
        wanted = (
            "issuer",
            "date",
            "amount",
            "invoice_number",
            "partner_name",
            "vat",
            "currency",
        )
        return [name for name in wanted if not extracted.get(name)]

    @staticmethod
    def _line_vals(rows):
        for i, row in enumerate(rows or []):
            if not isinstance(row, dict):
                continue
            yield {
                "sequence": i,
                "name": row.get("name") or row.get("description") or "",
                "product": row.get("product") or row.get("code"),
                "qty": _to_float(row.get("qty")),
                "uom": row.get("uom") or row.get("unece_code") or "",
                "price_unit": _to_float(row.get("price_unit")),
                "price_subtotal": _to_float(
                    row.get("price_subtotal") or row.get("price_total")
                ),
            }

    @staticmethod
    def _tax_line_vals(rows):
        for i, row in enumerate(rows or []):
            if not isinstance(row, dict):
                continue
            yield {
                "sequence": i,
                "name": row.get("name") or row.get("tax_id") or "",
                "base": _to_float(row.get("base")),
                "amount": _to_float(row.get("amount")),
                "unece_categ_code": row.get("unece_categ_code")
                or row.get("tax_code")
                or "",
            }


class Invoice2dataTemplatePreviewLine(models.TransientModel):
    _name = "invoice2data.template.preview.line"
    _description = "Invoice2data preview line"
    _order = "sequence, id"

    preview_id = fields.Many2one(
        "invoice2data.template.preview", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(default=10)
    # pylint: disable=attribute-string-redundant
    name = fields.Char(string="Description", readonly=True)
    product = fields.Char(string="Product / code", readonly=True)
    qty = fields.Float(string="Qty", readonly=True)
    uom = fields.Char(string="UoM", readonly=True)
    price_unit = fields.Float(string="Unit price", readonly=True)
    price_subtotal = fields.Float(string="Subtotal", readonly=True)


class Invoice2dataTemplatePreviewTax(models.TransientModel):
    _name = "invoice2data.template.preview.tax"
    _description = "Invoice2data preview tax line"
    _order = "sequence, id"

    preview_id = fields.Many2one(
        "invoice2data.template.preview", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Tax", readonly=True)
    unece_categ_code = fields.Char(string="UNECE code", readonly=True)
    base = fields.Float(readonly=True)
    amount = fields.Float(readonly=True)


# --- Coercion helpers -------------------------------------------------


def _to_date(value):
    """Coerce whatever invoice2data emitted for a date field to a Date."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if not value:
        return False
    if isinstance(value, str):
        # invoice2data usually normalises to ISO — accept but don't be
        # strict, the wizard is preview-only.
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y"):
            try:
                return datetime.strptime(value[: len(fmt) + 4], fmt).date()
            except ValueError:
                continue
    return False


def _to_float(value):
    if value in (None, "", False):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        try:
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return 0.0


def _dumps(obj):
    import json

    return json.dumps(obj, indent=2, default=str, ensure_ascii=False)
