# -*- coding: utf-8 -*-
# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
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
        purchase_reports = self._get_purchase_order_ubl_reports()
        if (
                report_name in purchase_reports and
                len(docids) == 1 and
                not self._context.get('no_embedded_ubl_xml')):
            order = self.env['purchase.order'].browse(docids[0])
            pdf_content = order.embed_ubl_xml_in_pdf(pdf_content=pdf_content)
        return pdf_content

    def _get_purchase_order_ubl_reports(self):
        return [
            'purchase.report_purchaseorder',
            'purchase.report_purchasequotation']
