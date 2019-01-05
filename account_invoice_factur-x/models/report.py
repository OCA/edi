# © 2016-2018 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api
from odoo.addons.account_facturx.models.ir_actions_report\
    import IrActionsReport as OriginIrActionsReport
import logging

logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
        # OVERRIDE
        if self.model == 'account.invoice' and res_ids and len(res_ids) == 1:
            invoice = self.env['account.invoice'].browse(res_ids)
            if invoice.type in ('out_invoice', 'out_refund') and\
               invoice.company_id.xml_format_in_pdf_invoice == 'factur-x':
                pdf_content = super(
                    OriginIrActionsReport, self)._post_pdf(
                    save_in_attachment, pdf_content=pdf_content,
                    res_ids=res_ids)
                pdf_content = invoice.regular_pdf_invoice_to_facturx_invoice(
                    pdf_content)
                return pdf_content
        return super(IrActionsReport, self)._post_pdf(
            save_in_attachment, pdf_content=pdf_content, res_ids=res_ids)
