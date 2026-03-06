# Copyright 2017-2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class Py3oReport(models.TransientModel):
    _inherit = "py3o.report"

    def _postprocess_report(self, model_instance, result_path):
        report = self.ir_actions_report_id
        if (
            self.env["ir.actions.report"]._is_invoice_report(report.report_name)
            and model_instance
            and len(model_instance) == 1
            and report.report_type == "py3o"
            and report.py3o_filetype == "pdf"
            and result_path
        ):
            move = model_instance
            # re-write PDF on result_path
            if move._xml_format_in_pdf_invoice() == "factur-x":
                move.regular_pdf_invoice_to_facturx_invoice(result_path)
        return super()._postprocess_report(model_instance, result_path)
