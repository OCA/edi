# Copyright 2017-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class Py3oReport(models.TransientModel):
    _inherit = "py3o.report"

    @api.model
    def _ubl_purchase_order_report_names(self):
        return ["purchase.report_purchaseorder", "purchase.report_purchasequotation"]

    def _postprocess_report(self, model_instance, result_path):
        purchase_reports = self._ubl_purchase_order_report_names()
        # We could match on object instead of report_name...
        # but I'm not sure it's a better approach
        if (
            self.ir_actions_report_id.report_name in purchase_reports
            and self.ir_actions_report_id.report_type == "py3o"
            and self.ir_actions_report_id.py3o_filetype == "pdf"
            and model_instance
            and result_path
        ):
            # re-write PDF on report_path
            model_instance.embed_ubl_xml_in_pdf(None, pdf_file=result_path)
        return super()._postprocess_report(model_instance, result_path)
