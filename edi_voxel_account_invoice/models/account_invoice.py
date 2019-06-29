# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, exceptions, models


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'voxel.mixin']

    voxel_enabled = fields.Boolean(
        compute='_compute_voxel_enabled',
        search='_search_voxel_enabled',
    )
    voxel_job_ids = fields.Many2many(
        comodel_name="queue.job",
        relation="account_invoice_voxel_job_rel",
        column1="invoice_id",
        column2="voxel_job_id",
        string="Jobs", copy=False)

    def get_voxel_login(self, company=None):
        """ This method overwrites the one defined in voxel.mixin to provide
        the login for this specific model (account.invoice)
        """
        return self.company_id.voxel_invoice_login_id

    @api.multi
    def _compute_voxel_enabled(self):
        for record in self:
            record.voxel_enabled = (record.company_id.voxel_enabled
                                    and record.partner_id.voxel_enabled)

    def _search_voxel_enabled(self, operator, value):
        return [
            ('company_id.voxel_enabled', operator, value),
            ('partner_id.voxel_enabled', operator, value),
        ]

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        self.action_send_to_voxel()
        return res

    @api.multi
    def action_cancel(self):
        jobs = self.mapped('voxel_job_ids')
        if not self._cancel_voxel_jobs(jobs):
            raise exceptions.Warning(_(
                'You can not cancel this invoice because'
                ' there is a job running!'))
        return super(AccountInvoice, self).action_cancel()

    @api.multi
    def action_send_to_voxel(self):
        types = ('out_invoice', 'out_refund')
        invoices = self.filtered(
            lambda inv: inv.type in types and inv.voxel_enabled)
        if invoices:
            invoices.enqueue_voxel_report(
                'edi_voxel_account_invoice.report_voxel_invoice')

    @api.multi
    def get_document_type(self):
        """ Document type name to be used in the name of the Voxel report"""
        return "Factura"
