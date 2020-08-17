# Copyright 2016-2017 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def postprocess_pdf_report(self, record, buffer):
        if self.is_ubl_xml_to_embed_in_invoice():
            buffer = record.add_xml_in_pdf_buffer(buffer)
        return super().postprocess_pdf_report(record, buffer)

    def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
        """We go through that method when the PDF is generated for the 1st
        time and also when it is read from the attachment.
        """
        pdf_content = super()._post_pdf(
            save_in_attachment, pdf_content=pdf_content, res_ids=res_ids
        )
        if res_ids and len(res_ids) == 1:
            if self.is_ubl_xml_to_embed_in_invoice():
                invoice = self.env["account.move"].browse(res_ids)
                if invoice.is_ubl_sale_invoice_posted():
                    pdf_content = invoice.embed_ubl_xml_in_pdf(pdf_content)
        return pdf_content

    def render_qweb_pdf(self, res_ids=None, data=None):
        """This is only necessary when tests are enabled.
        It forces the creation of pdf instead of html."""
        if isinstance(res_ids, int):
            res_ids = [res_ids]
        if len(res_ids or []) == 1 and not self.env.context.get("no_embedded_ubl_xml"):
            if len(self) == 1 and self.is_ubl_xml_to_embed_in_invoice():
                self = self.with_context(force_report_rendering=True)
        return super().render_qweb_pdf(res_ids, data)

    def is_ubl_xml_to_embed_in_invoice(self):
        return (
            self.model == "account.move"
            and not self.env.context.get("no_embedded_ubl_xml")
            and self.report_name in self._get_invoice_reports_ubl()
        )

    @classmethod
    def _get_invoice_reports_ubl(cls):
        return [
            "account.report_invoice",
            "account.report_invoice_with_payments",
            "account.account_invoice_report_duplicate_main",
        ]
