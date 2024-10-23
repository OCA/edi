# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from base64 import b64encode

from odoo import models


class BaseimportpdfbytemplateAccountMixin(models.AbstractModel):
    _inherit = "baseimportpdfbytemplate.mixin"
    _name = "baseimportpdfbytemplate.account.mixin"
    _description = "Functions for baseimportpdfbytemplate account mixin documents"

    def _import_invoice_base_import_pdf_by_template(
        self, invoice, file_data, new=False
    ):
        """Method to process the PDF with base_import_pdf_by_template_account
        if any template is available (similar to account_edi_ubl_cii)."""
        template_model = self.env["base.import.pdf.template"].with_company(
            invoice.company_id.id
        )
        total_templates = template_model.search_count([("model", "=", invoice._name)])
        if total_templates == 0:
            return False
        # We need to create the attachment that we will use in the wizard because it
        # has not been created yet.
        attachment = self.env["ir.attachment"].create(
            {"name": file_data["filename"], "datas": b64encode(file_data["content"])}
        )
        invoice.move_type = (
            "in_invoice" if invoice.journal_id.type == "purchase" else "out_invoice"
        )
        self = self.with_context(default_move_type=invoice.move_type)
        return self._import_record_base_import_pdf_by_template(invoice, attachment)
