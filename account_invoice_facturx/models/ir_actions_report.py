# Copyright 2016-2022 Akretion France (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

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
        if (
            collected_streams
            and res_ids
            and len(res_ids) == 1
            and self._is_invoice_report(report_ref)
            and not self.env.context.get("no_embedded_factur-x_xml")
        ):
            move = amo.browse(res_ids)
            if move._xml_format_in_pdf_invoice() == "factur-x":
                pdf_bytesio = collected_streams[move.id]["stream"]
                move.regular_pdf_invoice_to_facturx_invoice(pdf_bytesio)
        return collected_streams
