# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# Copyright 2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def postprocess_pdf_report(self, record, buffer):
        if self.is_ubl_xml_to_embed_in_purchase_order():
            buffer = record.add_xml_in_pdf_buffer(buffer)
        return super().postprocess_pdf_report(record, buffer)

    def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
        """
        We go through that method when the PDF is generated for the 1st
        time and also when it is read from the attachment.
        """
        pdf_content = super()._post_pdf(
            save_in_attachment, pdf_content=pdf_content, res_ids=res_ids
        )
        if res_ids and len(res_ids) == 1:
            if self.is_ubl_xml_to_embed_in_purchase_order():
                purchase_order = self.env["purchase.order"].browse(res_ids)
                pdf_content = purchase_order.embed_ubl_xml_in_pdf(pdf_content)
        return pdf_content

    def _render_qweb_pdf(self, res_ids=None, data=None):
        """
        This is only necessary when tests are enabled.
        It forces the creation of pdf instead of html."""
        if len(res_ids or []) == 1 and not self.env.context.get("no_embedded_ubl_xml"):
            if len(self) == 1 and self.is_ubl_xml_to_embed_in_purchase_order():
                self = self.with_context(force_report_rendering=True)
        return super()._render_qweb_pdf(res_ids, data)

    def is_ubl_xml_to_embed_in_purchase_order(self):
        return (
            self.model == "purchase.order"
            and not self.env.context.get("no_embedded_ubl_xml")
            and self.report_name in self._get_purchase_order_ubl_reports()
        )

    def _get_purchase_order_ubl_reports(self):
        return ["purchase.report_purchaseorder", "purchase.report_purchasequotation"]
