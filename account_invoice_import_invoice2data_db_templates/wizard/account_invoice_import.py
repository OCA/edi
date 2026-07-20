# Copyright 2025-2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Merge DB-stored invoice2data templates into the import wizard.

Extends the wizard contributed by ``account_invoice_import_invoice2data``
to append the active DB templates to the list passed into
``invoice2data.extract_data``.
"""

import logging
import os
import shutil
from tempfile import NamedTemporaryFile

from odoo import _, api, models, tools
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)

try:
    from invoice2data import extract_data
    from invoice2data.extract.loader import read_templates
except ImportError:  # pragma: no cover
    extract_data = None
    read_templates = None


class AccountInvoiceImport(models.TransientModel):
    _inherit = "account.invoice.import"

    @api.model
    def invoice2data_parse_invoice(self, file_data, company):
        """Reimplement the wizard's hook to merge DB templates."""
        if extract_data is None or read_templates is None:
            # Lib missing: propagate the upstream error path.
            return super().invoice2data_parse_invoice(file_data, company)

        logger.info("Trying to analyze PDF invoice with invoice2data lib + DB")
        with NamedTemporaryFile(
            "wb", prefix="odoo-aii-inv2data-pdf-", suffix=".pdf"
        ) as fileobj:
            fileobj.write(file_data)
            fileobj.flush()
            templates = self._invoice2data_collect_templates()
            try:
                result = extract_data(fileobj.name, templates=templates)
            except Exception as exc:  # noqa: BLE001
                raise UserError(
                    _("PDF Invoice parsing failed. Error message: %s") % exc
                ) from exc
            if not result:
                result = self._invoice2data_try_tesseract(fileobj.name, templates)
            if not result:
                return False
        return self.invoice2data_to_parsed_inv(result)

    @api.model
    def _invoice2data_collect_templates(self):
        """Build the (disk + DB) template list passed to ``extract_data``."""
        templates = []
        local_dir = tools.config.get("invoice2data_templates_dir", False)
        if local_dir and os.path.isdir(local_dir):
            templates += read_templates(local_dir)
        exclude_built_in = tools.config.get(
            "invoice2data_exclude_built_in_templates", False
        )
        if not exclude_built_in:
            templates += read_templates()
        templates += self.env["invoice2data.template"].get_templates(
            "purchase_invoice"
        )
        return templates

    def _invoice2data_try_tesseract(self, path, templates):
        """OCR fallback path, mirroring the upstream wizard's behaviour."""
        if not shutil.which("tesseract"):
            logger.warning("Tesseract fallback unavailable; install tesseract-ocr")
            return False
        logger.info("Falling back on Tesseract OCR")
        try:
            from invoice2data.input import tesseract
        except ImportError:
            return False
        try:
            return extract_data(path, templates=templates, input_module=tesseract)
        except Exception:  # noqa: BLE001
            logger.exception("Tesseract fallback failed for %s", path)
            return False
