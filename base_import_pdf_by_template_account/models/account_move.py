# Copyright 2024-2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _import_base_import_pdf_by_template(self, invoice, file_data, new=False):
        """Method to process the PDF with base_import_pdf_by_template_account
        if any template is available (similar to account_edi_ubl_cii)."""
        template_model = self.env["base.import.pdf.template"].with_company(
            invoice.company_id.id
        )
        total_templates = template_model.search_count([("model", "=", invoice._name)])
        if total_templates == 0:
            return False
        wizard = self.env["wizard.base.import.pdf.upload"].create(
            {
                "model": invoice._name,
                "record_ref": f"{invoice._name},{invoice.id}",
                "attachment_ids": [(6, 0, file_data["attachment"].ids)],
            }
        )
        wizard.with_context(skip_template_not_found_error=True).action_process()
        return True

    def _get_edi_decoder(self, file_data, new=False):
        if file_data["type"] == "pdf":
            return self._import_base_import_pdf_by_template
        return super()._get_edi_decoder(file_data, new=new)
