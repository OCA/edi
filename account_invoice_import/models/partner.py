# -*- coding: utf-8 -*-
# © 2015-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_import_id = fields.Many2one(
        'account.invoice.import.config',
        string='Invoice Import Configuration',
        company_dependent=True)

    def invoice_import2import_config(self):
        self.ensure_one()
        if not self.invoice_import_id:
            raise UserError(_(
                "Missing Invoice Import Configuration on partner '%s'.")
                % self.name_get()[0][1])
        config = self.invoice_import_id
        vals = {
            'invoice_line_method': config.invoice_line_method,
            'account_analytic': config.account_analytic_id or False,
            }
        if config.invoice_line_method == '1line_no_product':
            vals['account'] = config.account_id
            vals['taxes'] = config.tax_ids
            vals['label'] = config.label or False
        elif config.invoice_line_method == '1line_static_product':
            vals['product'] = config.product_id
            vals['label'] = config.label or False
        elif config.invoice_line_method == 'nline_no_product':
            vals['account'] = config.account_id
        elif config.invoice_line_method == 'nline_static_product':
            vals['product'] = config.product_id
        return vals
