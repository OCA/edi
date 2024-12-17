# SPDX-FileCopyrightText: 2021 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import io
import logging
import zipfile

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval, time

_logger = logging.getLogger(__name__)

ATTACHMENT_TMP_DESC = "temporary-invoice-edi-zip-file"
ZIP_FILE_NAME = "invoice_files-{timestamp}.zip"
REPORT_REF = "account.account_invoices"


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_invoice_pdf(self):
        report = self.env.ref(REPORT_REF)
        report_name = safe_eval(
            report.print_report_name, {"object": self, "time": time}
        )
        filename = "{}.pdf".format(report_name.replace("/", "_"))
        report_contents = report._render_qweb_pdf([self.id])[0]
        return filename, report_contents

    def _add_invoice_edi_files(self, ziparc):
        # first, the pdf must be generated, because some of the edi documents
        # will be embedded in it, while others will embed the pdf in them.
        pdf_filename, pdf_contents = self._get_invoice_pdf()
        ziparc.writestr(pdf_filename, pdf_contents)
        # now, add all edi documents that are not embedded in the pdf.
        for edi_document in self.edi_document_ids:
            if edi_document.edi_format_id._is_embedding_to_invoice_pdf_needed():
                # already present in the pdf
                continue
            attachment = edi_document.attachment_id
            ziparc.writestr(attachment.name, attachment.raw)

    def download_edi_files_zip(self):
        """
        Create a zip file with the EDI documents and the PDF for each invoice.
        """
        for invoice in self:
            # fail fast
            if (
                invoice.move_type not in ("out_invoice", "out_refund")
                or invoice.state != "posted"
            ):
                raise UserError(
                    _(
                        "Cannot generate file because invoice {invoice_name} "
                        "is not an invoice or a refund or that invoice is "
                        "not posted."
                    ).format(invoice_name=invoice.name)
                )
        with io.BytesIO() as buffer:
            with zipfile.ZipFile(
                buffer, mode="w", compression=zipfile.ZIP_DEFLATED
            ) as ziparc:
                for invoice in self:
                    invoice._add_invoice_edi_files(ziparc)
            zip_filename = ZIP_FILE_NAME.format(
                timestamp=fields.Datetime.now().isoformat().replace(":", "-"),
            )
            attachment = self.env["ir.attachment"].create(
                {
                    "name": zip_filename,
                    "description": ATTACHMENT_TMP_DESC,
                    "raw": buffer.getvalue(),
                    "type": "binary",
                }
            )
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/ir.attachment/{}/datas?download=true".format(
                attachment.id
            ),
            "target": "self",
        }

    def _cron_remove_tmp_edi_zip_files(self):
        """
        Find temporary zipped file created and delete it.
        """
        _logger.info("Removing temporary EDI zip files")
        self.env["ir.attachment"].search(
            [("description", "=", ATTACHMENT_TMP_DESC)]
        ).unlink()
