# Copyright 2020 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os, base64

from odoo import models, fields, api, _


class ExportMultiEdifactInvoiceWizard(models.TransientModel):
    _name = 'export.multi.edifact.invoice.wizard'

    state = fields.Selection([
        ('init', 'Init'),
        ('with_errors', 'With Errors'),
        ('done', 'Done')
    ], readonly=True, default='init')
    unexported_invoice_ids = fields.Many2many(
        'account.invoice', 'account_invoice_exported_edifact_wizard_rel',
        string='Unexported Invoices', readonly=True)

    @api.multi
    def export_multi_edifact_invoice(self):
        invoice_obj = self.env['account.invoice']

        unexported_invoice_ids = []

        invoices = []
        state = 'done'
        if self._context['active_model'] == 'account.invoice'\
                and self._context['active_ids']:
            invoices = invoice_obj.browse(self._context['active_ids'])
        for invoice in invoices:
            try:
                invoice.invoice_export_edifact()
            except Exception as e:
                unexported_invoice_ids.append(invoice.id)
                state = 'with_errors'
                continue
        self.write({
            'state': state,
            'unexported_invoice_ids': [(6, 0, unexported_invoice_ids)],
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Export Edifact Invoices'),
            'res_model': self._name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }
