# Copyright 2016-2017 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api
import logging

logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    @api.multi
    def render_qweb_pdf(self, res_ids=None, data=None):
        """We go through that method when the PDF is generated for the 1st
        time and also when it is read from the attachment.
        This method is specific to QWeb"""
        pdf_content = super(IrActionsReport, self).render_qweb_pdf(
            res_ids, data)
        invoice_reports = self._get_invoice_reports_ubl()
        if (
                len(self) == 1 and
                self.report_name in invoice_reports and
                len(res_ids) == 1 and
                not self._context.get('no_embedded_ubl_xml')):
            invoice = self.env['account.invoice'].browse(res_ids[0])
            if (
                    invoice.type in ('out_invoice', 'out_refund') and
                    invoice.company_id.xml_format_in_pdf_invoice == 'ubl'):
                pdf_content = invoice.with_context(
                    no_embedded_pdf=True).embed_ubl_xml_in_pdf(
                    pdf_content=pdf_content)
        return pdf_content

    @classmethod
    def _get_invoice_reports_ubl(cls):
        return [
            'account.report_invoice',
            'account.report_invoice_with_payments',
            'account.account_invoice_report_duplicate_main']
