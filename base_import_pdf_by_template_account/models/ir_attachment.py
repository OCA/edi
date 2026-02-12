# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    # TODO: Remove in v19 because _extend_with_attachments() method is properly done
    # in account.document.import.mixin
    def _unwrap_edi_attachments(self):
        to_process = super()._unwrap_edi_attachments()
        if len(to_process) > 1 and any(a["type"] == "pdf" for a in to_process):
            attachment = to_process[0]["attachment"]
            if attachment.res_model and attachment.res_id:
                record = self.env[attachment.res_model].browse(attachment.res_id)
                template_model = self.env["base.import.pdf.template"]
                if "company_id" in record._fields:
                    template_model = template_model.with_company(record.company_id.id)
                total_templates = template_model.search_count(
                    [("model", "=", record._name)]
                )
                if total_templates > 0:
                    # Define a sort_weight=1 to have a higher priority in the
                    # _extend_with_attachments() method when doing the decoder
                    for to_process_item in to_process:
                        if to_process_item["type"] == "pdf":
                            to_process_item["sort_weight"] = 1
                    to_process.sort(key=lambda x: x["sort_weight"])
        return to_process
