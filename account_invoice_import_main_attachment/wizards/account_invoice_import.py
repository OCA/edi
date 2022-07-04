# Copyright 2022 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

logger = logging.getLogger(__name__)


class AccountInvoiceImport(models.TransientModel):
    _inherit = "account.invoice.import"

    @api.model
    def default_get(self, fields_list):
        """Try to use main attachment for invoice."""
        res = super().default_get(fields_list)
        invoice_id = res.get("invoice_id", False)
        if invoice_id:
            res.update(self._default_main_attachment(invoice_id))
        return res

    @api.model
    def _default_main_attachment(self, invoice_id):
        """Try to get attachment from invoice."""
        result = {}
        move_model = self.env["account.move"]
        invoice = move_model.browse(invoice_id)
        if invoice and invoice.message_main_attachment_id:
            attachment = invoice.message_main_attachment_id
            result["invoice_filename"] = attachment.name or "main-attachment"
            result["invoice_file"] = attachment.datas
        return result

    @api.model
    def _prepare_update_invoice_vals(self, parsed_inv, invoice):
        """Add invoice lines if not present already."""
        vals = super()._prepare_update_invoice_vals(parsed_inv, invoice)
        if invoice and not invoice.line_ids:
            vals["invoice_line_ids"] = []
            import_config = self.import_config_id.convert_to_import_config()
            self._prepare_line_vals_1line(
                invoice.partner_id, vals, parsed_inv, import_config
            )
        return vals

    def update_invoice(self):
        """Can override partner in invoice, if not set already."""
        self.ensure_one()
        invoice = self.invoice_id
        parsed_inv = self.get_parsed_invoice()
        partner = self._match_partner(
            parsed_inv["partner"], parsed_inv["chatter_msg"], partner_type="supplier"
        )
        if partner and not invoice.partner_id:
            invoice.write({"partner_id": partner.id})
        return super().update_invoice()
