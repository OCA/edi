# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

SUPPORTED_FILE_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.oasis.opendocument.spreadsheet": ".ods",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "image/jpeg": ".jpeg",
    "image/png": ".png",
    "text/csv": ".csv",
}


class AccountEdiCommon(models.AbstractModel):

    _inherit = "account.edi.common"

    def _import_invoice(self, journal, filename, tree, existing_invoice=None):
        invoice = super()._import_invoice(
            journal, filename, tree, existing_invoice=existing_invoice
        )
        additional_docs = tree.findall("./{*}AdditionalDocumentReference")
        for document in additional_docs:
            attachment_name = document.find("{*}ID")
            attachment_data = document.find(
                "{*}Attachment/{*}EmbeddedDocumentBinaryObject"
            )
            if attachment_data is None:
                continue
            mime_code = attachment_data.attrib.get("mimeCode")
            if mime_code == "application/pdf":
                # already covered by base module
                continue
            if not (extension := SUPPORTED_FILE_TYPES.get(mime_code)):
                continue
            text = attachment_data.text
            name = (attachment_name.text or "invoice").split("\\")[-1].split("/")[
                -1
            ].split(".")[0] + extension
            self.env["ir.attachment"].create(
                {
                    "name": name,
                    "res_id": invoice.id,
                    "res_model": "account.move",
                    "datas": text + "=" * (len(text) % 3),  # Fix incorrect padding
                    "type": "binary",
                    "mimetype": mime_code,
                }
            )
        return invoice
