# Copyright 2016-2022 Akretion France (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    # In v11, it won't work if I inherit _post_pdf() because v11 doesn't contain
    # this line of code that v12 has:
    # https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/models/ir_actions_report.py#L640

    @api.multi
    def render_qweb_pdf(self, res_ids=None, data=None):
        """We go through that method when the PDF is generated for the 1st
        time and also when it is read from the attachment.
        This method is specific to QWeb"""
        pdf_content, file_format = super().render_qweb_pdf(res_ids=res_ids, data=data)
        aio = self.env['account.invoice']
        invoice_reports = aio._get_invoice_report_names()
        if (
                file_format == 'pdf' and
                len(self) == 1 and
                self.report_name in invoice_reports and
                res_ids and
                len(res_ids) == 1 and
                not self._context.get('no_embedded_factur-x_xml')):
            inv = aio.browse(res_ids[0])
            if (
                    inv.type in ('out_invoice', 'out_refund') and
                    inv.company_id.xml_format_in_pdf_invoice == 'factur-x'):
                pdf_content = inv.regular_pdf_invoice_to_facturx_invoice(
                    pdf_content=pdf_content)
        return pdf_content, file_format
