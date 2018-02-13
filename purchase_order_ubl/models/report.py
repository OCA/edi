# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class Report(models.Model):
    _inherit = "ir.actions.report"

    @api.multi
    def render_qweb_pdf(self, res_ids=None, data=None):
        """We go through that method when the PDF is generated for the 1st
        time and also when it is read from the attachment.
        This method is specific to QWeb"""
        pdf_content = super(Report, self).render_qweb_pdf(res_ids, data)
        purchase_reports = [
            'purchase.report_purchaseorder',
            'purchase.report_purchasequotation']
        if (
                len(self) == 1 and
                self.report_name in purchase_reports and
                len(res_ids) == 1 and
                not self._context.get('no_embedded_ubl_xml')):
            order = self.env['purchase.order'].browse(res_ids[0])
            pdf_content = order.embed_ubl_xml_in_pdf(pdf_content=pdf_content)
        return pdf_content
