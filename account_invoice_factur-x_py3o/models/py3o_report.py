# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api
import logging
logger = logging.getLogger(__name__)

try:
    from facturx import generate_facturx_from_file
except ImportError:
    logger.debug('Cannot import facturx')


class Py3oReport(models.TransientModel):
    _inherit = 'py3o.report'

    @api.model
    def _postprocess_report(self, report_path, res_id, save_in_attachment):
        invoice_reports = [
            'account.report_invoice',
            'account.account_invoice_report_duplicate_main']
        # We could match on object instead of report_name...
        # but I'm not sure it's a better approach
        if (
                self.ir_actions_report_xml_id.report_name
                in invoice_reports and
                res_id and
                report_path):
            invoice = self.env['account.invoice'].browse(res_id)
            # re-write PDF on report_path
            if invoice.type in ('out_invoice', 'out_refund'):
                facturx_xml_str, level = invoice.generate_facturx_xml()
                pdf_metadata = invoice._prepare_pdf_metadata()
                generate_facturx_from_file(
                    report_path, facturx_xml_str, check_xsd=False,
                    facturx_level=level, pdf_metadata=pdf_metadata)
        return super(Py3oReport, self)._postprocess_report(
            report_path, res_id, save_in_attachment)
