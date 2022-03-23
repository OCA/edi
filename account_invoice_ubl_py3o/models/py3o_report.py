# © 2022 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class Py3oReport(models.TransientModel):
    _inherit = "py3o.report"

    @api.model
    def _postprocess_report(self, model_instance, result_path):
        inv_reports = [
            "account.report_invoice_with_payments",
            "account.report_invoice",
        ]
        # We could match on object instead of report_name...
        # but I'm not sure it's a better approach
        if (
            self.ir_actions_report_id.report_name in inv_reports
            and self.ir_actions_report_id.report_type == "py3o"
            and self.ir_actions_report_id.py3o_filetype == "pdf"
            and result_path
            and model_instance.company_id.xml_format_in_pdf_invoice == "ubl"
        ):
            if (
                model_instance.move_type in ("out_invoice", "out_refund")
                and model_instance.company_id.xml_format_in_pdf_invoice == "ubl"
            ):
                # re-write PDF on report_path
                model_instance.with_context(no_embedded_pdf=True).embed_ubl_xml_in_pdf(
                    None, pdf_file=result_path
                )
        return super()._postprocess_report(model_instance, result_path)
