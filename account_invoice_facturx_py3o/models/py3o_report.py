# Copyright 2017-2020 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
import logging
logger = logging.getLogger(__name__)

try:
    from facturx import generate_facturx_from_file
except ImportError:
    logger.debug('Cannot import facturx')


class Py3oReport(models.TransientModel):
    _inherit = 'py3o.report'

    @api.multi
    def _postprocess_report(self, model_instance, result_path):
        aio = self.env['account.invoice']
        invoice_reports = aio._get_invoice_report_names()
        if (
                self.ir_actions_report_id.report_name
                in invoice_reports and
                model_instance and
                len(model_instance) == 1 and
                self.ir_actions_report_id.report_type == 'py3o' and
                self.ir_actions_report_id.py3o_filetype == 'pdf' and
                result_path):
            invoice = model_instance
            # re-write PDF on result_path
            if (
                    invoice.type in ('out_invoice', 'out_refund') and
                    invoice.company_id.xml_format_in_pdf_invoice ==
                    'factur-x'):
                facturx_xml_str, level = invoice.generate_facturx_xml()
                pdf_metadata = invoice._prepare_pdf_metadata()
                generate_facturx_from_file(
                    result_path, facturx_xml_str, check_xsd=False,
                    facturx_level=level, pdf_metadata=pdf_metadata)
        return super()._postprocess_report(model_instance, result_path)
