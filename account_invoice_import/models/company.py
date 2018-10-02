# Copyright 2017-2018 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    adjustment_credit_account_id = fields.Many2one(
        'account.account', string='Adjustment Credit Account',
        domain=[('deprecated', '=', False)])
    adjustment_debit_account_id = fields.Many2one(
        'account.account', string='Adjustment Debit Account',
        domain=[('deprecated', '=', False)])
    invoice_import_email = fields.Char(
        'Mail Gateway: Destination E-mail',
        help="This field is used in multi-company setups to import the "
        "invoices received by the mail gateway in the appropriate company")

    _sql_constraints = [(
        'invoice_import_email_uniq',
        'unique(invoice_import_email)',
        'This invoice import email already exists!')]
