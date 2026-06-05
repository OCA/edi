# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models


class AccountMove(models.Model):

    _inherit = "account.move"

    purchase_mismatch = fields.Boolean(
        compute="_compute_purchase_mismatch",
        help=(
            "Checked when this invoice has at least one line that does not fully "
            "match its related purchase order line."
        ),
    )
    purchase_mismatch_details = fields.Text(
        compute="_compute_purchase_mismatch",
        help=(
            "Human-readable description of the differences between invoice lines "
            "and their related purchase order lines."
        ),
    )

    @api.depends(
        "invoice_line_ids.purchase_line_mismatch",
        "invoice_line_ids.purchase_line_mismatch_details",
        "invoice_line_ids.product_id",
        "invoice_line_ids.name",
    )
    def _compute_purchase_mismatch(self):
        for rec in self:
            mismatch_lines = rec.invoice_line_ids.filtered("purchase_line_mismatch")

            if not mismatch_lines:
                rec.purchase_mismatch = False
                rec.purchase_mismatch_details = False
                continue

            rec.purchase_mismatch = True

            purchase_mismatch_details = _(
                "The following differences were detected between this invoice and its "
                "related purchase order lines:\n"
            )
            for line in mismatch_lines:
                product_label = (
                    line.product_id.display_name or line.name or _("No product")
                )
                purchase_mismatch_details += product_label + "\n"
                purchase_mismatch_details += line.purchase_line_mismatch_details + "\n"
            rec.purchase_mismatch_details = purchase_mismatch_details

    def _link_invoice_origin_to_purchase_orders(self, timeout=10):
        # disable standard purchase linking
        return self

    def _get_po_sequence_prefix(self):
        """return the prefix used by purchase order sequence"""
        seq = (
            self.env["ir.sequence"]
            .sudo()
            .search([("code", "=", "purchase.order")], limit=1)
        )
        if not seq:
            return "PO"
        prefix = seq.prefix or ""
        match = re.match(r"([A-Za-z]+)", prefix)
        if match:
            return match.group(1)
        return "PO"

    def _extract_purchase_references_from_origin(self, invoice_origin=None):
        invoice_origin = invoice_origin if invoice_origin else self.invoice_origin
        if not invoice_origin:
            return []
        prefix = self._get_po_sequence_prefix()
        # flake8: noqa: E231
        pattern = rf"(?:#)?({re.escape(prefix)}[-/\s]?\d+(?:[-/\s]?\d+)*)"
        matches = re.findall(pattern, invoice_origin, flags=re.IGNORECASE)
        normalized = []
        for match in matches:
            value = re.sub(r"[\s#]", "", match).upper()
            normalized.append(value)
        return list(dict.fromkeys(normalized))
