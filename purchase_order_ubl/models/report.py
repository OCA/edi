# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class Report(models.Model):
    _inherit = "ir.actions.report"

    @api.multi
    def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
        """We go through that method when the PDF is generated for the 1st
        time and also when it is read from the attachment.
        This method is specific to QWeb"""
        purchase_reports = self._get_purchase_order_ubl_reports()
        if (
                len(self) == 1 and
                self.report_name in purchase_reports and
                res_ids and
                len(res_ids) == 1 and
                not self._context.get('no_embedded_ubl_xml')):
            order = self.env['purchase.order'].browse(res_ids[0])
            pdf_content = order.embed_ubl_xml_in_pdf(pdf_content=pdf_content)
        return super()._post_pdf(
            save_in_attachment, pdf_content=pdf_content, res_ids=res_ids)

    def _get_purchase_order_ubl_reports(self):
        return [
            'purchase.report_purchaseorder',
            'purchase.report_purchasequotation']
