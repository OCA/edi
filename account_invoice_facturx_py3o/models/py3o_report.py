# Copyright 2017-2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class Py3oReport(models.TransientModel):
    _inherit = "py3o.report"

    def _postprocess_report(self, model_instance, result_path):
        amo = self.env["account.move"]
        invoice_reports = amo._get_invoice_report_names()
        if (
            self.ir_actions_report_id.report_name in invoice_reports
            and model_instance
            and len(model_instance) == 1
            and self.ir_actions_report_id.report_type == "py3o"
            and self.ir_actions_report_id.py3o_filetype == "pdf"
            and result_path
        ):
            move = model_instance
            # re-write PDF on result_path
            if move._xml_format_in_pdf_invoice() == "factur-x":
                move.regular_pdf_invoice_to_facturx_invoice(result_path)
        return super()._postprocess_report(model_instance, result_path)
