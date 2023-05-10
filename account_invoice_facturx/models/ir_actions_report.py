# Copyright 2016-2023 Akretion France (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        # It works, but:
        # - when you click on the "Print" button or use the "Print" menu,
        # the XML file is regenerated even when the invoice is read from the attachment.
        # - when you open the invoice from the attachment, you get the "original" XML file
        collected_streams = super()._render_qweb_pdf_prepare_streams(
            report_ref, data, res_ids=res_ids
        )
        amo = self.env["account.move"]
        invoice_reports = amo._get_invoice_report_names()
        if (
            collected_streams
            and report_ref in invoice_reports
            and res_ids
            and len(res_ids) == 1
            and not self.env.context.get("no_embedded_factur-x_xml")
        ):
            inv = amo.browse(res_ids)
            if inv._xml_format_in_pdf_invoice() == "factur-x":
                # Add the attachments to the pdf file
                pdf_stream = collected_streams[inv.id]["stream"]
                # Read pdf content
                pdf_content = pdf_stream.getvalue()
                inv.regular_pdf_invoice_to_facturx_invoice(pdf_content=pdf_content)
        return collected_streams
