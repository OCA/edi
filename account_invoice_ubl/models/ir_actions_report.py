# Copyright 2016-2017 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        # It works, but:
        # - when you click on the "Print" button or use the "Print" menu,
        # the XML file is regenerated even when the invoice is read from the attachment.
        # - when you open the invoice from the attachment, you get the "original" XML
        # file
        collected_streams = super()._render_qweb_pdf_prepare_streams(
            report_ref, data, res_ids=res_ids
        )
        amo = self.env["account.move"]
        invoice_reports = amo._get_invoice_report_names()
        report_name = self._get_report(report_ref).report_name
        if (
            collected_streams
            and res_ids
            and len(res_ids) == 1
            and report_name in invoice_reports
            and not self.env.context.get("no_embedded_ubl_xml")
        ):
            move = amo.browse(res_ids)
            if move._xml_format_in_pdf_invoice() == "ubl":
                pdf_stream = collected_streams[move.id]
                move._embed_ubl_xml_in_pdf(pdf_stream)
        return collected_streams
