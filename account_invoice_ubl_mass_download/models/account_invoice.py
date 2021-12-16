# Copyright 2021 Coop IT Easy (https://coopiteasy.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io
import logging
import zipfile

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

ATTACHMENT_TMP_NAME = "temporary-invoice-ubl-zip-file"
ZIP_FILE_NAME = "XML-UBL-PDF"


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.multi
    def zip_ubl_xml_and_pdf(self):
        """
        Create a zip file with XML UBL and PDF for each invoice.
        """
        with io.BytesIO() as buffer:
            with zipfile.ZipFile(
                buffer, mode="w", compression=zipfile.ZIP_DEFLATED
            ) as ziparc:
                for invoice in self:
                    if (
                        invoice.type
                        not in (
                            "out_invoice",
                            "out_refund",
                        )
                        or invoice.state not in ("open", "paid")
                    ):
                        raise UserError(
                            _(
                                "Cannot generate file because Invoice {} "
                                "is not an invoice or a refund or that invoice "
                                "is not open or paid status." % invoice.name
                            )
                        )
                    # XML UBL
                    version = invoice.get_ubl_version()
                    xml_string = invoice.generate_ubl_xml_string(version=version)
                    xmlname = "{}-{}".format(
                        invoice.number.replace("/", "-"),
                        invoice.get_ubl_filename(version=version),
                    )
                    ziparc.writestr(xmlname, xml_string)
                    # PDF
                    reportinv = (
                        self.env["ir.actions.report"]
                        ._get_report_from_name("account.report_invoice_with_payments")
                        .render_qweb_pdf([invoice.id])
                    )
                    invpdf = reportinv[0]
                    pdfname = "{}.pdf".format(
                        invoice.number.replace("/", "-"),
                    )
                    ziparc.writestr(pdfname, invpdf)
            ctx = {}
            zipname = "{}-{}.zip".format(
                ZIP_FILE_NAME,
                fields.Datetime.now().isoformat().replace(":", "-"),
            )
            attach = (
                self.env["ir.attachment"]
                .with_context(ctx)
                .create(
                    {
                        "name": ATTACHMENT_TMP_NAME,
                        "datas": base64.b64encode(buffer.getvalue()),
                        "datas_fname": zipname,
                        "type": "binary",
                    }
                )
            )
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/ir.attachment/{}/datas?download=true".format(
                attach.id
            ),
            "target": "self",
        }

    def _cron_remove_ubl_zip(self):
        """
        Find temporary zipped file created and delete it.
        """
        _logger.info("Running autovacuum UBL zipped file.")
        attachs = self.env["ir.attachment"].search([("name", "=", ATTACHMENT_TMP_NAME)])
        attachs.unlink()
