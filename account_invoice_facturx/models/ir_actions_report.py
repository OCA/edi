# Copyright 2016-2021 Akretion France (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
        """We go through that method when the PDF is generated for the
        1st time (res_id has a value) and also
        when it is read from the attachment (res_ids=None).
        This method is specific to QWeb"""
        amo = self.env["account.move"]
        invoice_reports = amo._get_invoice_report_names()
        if (
            len(self) == 1
            and self.report_name in invoice_reports
            and res_ids
            and len(res_ids) == 1
            and not self.env.context.get("no_embedded_factur-x_xml")
        ):
            inv = amo.browse(res_ids[0])
            if inv._xml_format_in_pdf_invoice() == "factur-x":
                pdf_content = inv.regular_pdf_invoice_to_facturx_invoice(
                    pdf_content=pdf_content
                )
        return super()._post_pdf(
            save_in_attachment, pdf_content=pdf_content, res_ids=res_ids
        )
