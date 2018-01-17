# -*- coding: utf-8 -*-
# © 2016-2018 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api
import logging

logger = logging.getLogger(__name__)


class Report(models.Model):
    _inherit = 'report'

    @api.model
    def get_pdf(self, docids, report_name, html=None, data=None):
        """We go through that method when the PDF is generated for the 1st
        time and also when it is read from the attachment.
        This method is specific to QWeb"""
        pdf_content = super(Report, self).get_pdf(
            docids, report_name, html=html, data=data)
        invoice_reports = [
            'account.report_invoice',
            'account.account_invoice_report_duplicate_main']
        if report_name in invoice_reports and len(docids) == 1:
            invoice = self.env['account.invoice'].browse(docids[0])
            if (
                    invoice.type in ('out_invoice', 'out_refund') and
                    invoice.company_id.xml_format_in_pdf_invoice ==
                    'factur-x'):
                pdf_content = invoice.regular_pdf_invoice_to_facturx_invoice(
                    pdf_content=pdf_content)
        return pdf_content

# TODO : the PDF saved as attachment is NOT the good one...
# but the PDF opened from the attachment is OK !
# because we don't inherit the right method.
# get_pdf() calls _run_wkhtmltopdf() which generate
# AND SAVE AS ATTACHMENT the report. So we need a hook inside _run_wkhtmltopdf
# but there is no hook for the moment
# The problem is the same in the module
# OCA/reporting-engines/report_qweb_signer
