# -*- coding: utf-8 -*-
# © 2016-2018 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api
import logging

logger = logging.getLogger(__name__)


class Report(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
        """
        - laisse le comportement natif de _post_pdf pour tous les rapports
        - renvoie le PDF Factur-X enrichi uniquement pour les factures concernées
        Cette surcharge est effectuée car, si l'on utilise uniquement super, on obtient uniquement le PDF sans XML.
        """

        facturx_pdf = None

        if (
                pdf_content and
                len(self) == 1 and
                res_ids and
                len(res_ids) == 1 and
                not self.env.context.get('no_embedded_factur-x_xml')
        ):
            invoice = self.env['account.invoice'].browse(res_ids[0])

            if (
                    invoice.type in ('out_invoice', 'out_refund')
                    and invoice.company_id.xml_format_in_pdf_invoice == 'factur-x'
            ):

                facturx_pdf = invoice.regular_pdf_invoice_to_facturx_invoice(
                    pdf_content=pdf_content
                )

        if facturx_pdf:
            return facturx_pdf

        return super(Report, self)._post_pdf(
            save_in_attachment,
            pdf_content=pdf_content,
            res_ids=res_ids
        )