# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, _
from odoo.exceptions import UserError
import logging

logger = logging.getLogger(__name__)


class AccountInvoiceDownloadConfig(models.Model):
    _name = 'account.invoice.download.config'
    _description = 'Configuration for the download of Supplier Invoices'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'account.invoice.download.config'))
    invoice_import_id = fields.Many2one(
        'account.invoice.import.config',
        string='Invoice Import Configuration', required=True)
    # partner_id = related field
    last_run = fields.Date(string='Last Download Date')
    # Don't set last_run as readonly because sometimes we need to
    # manually fool the system so that he starts downloading from
    # another date than the last download date
    method = fields.Selection([
        ('manual', 'Manual'),
        ('auto', 'Automatic'),
        ], string='Download Method', required=True, default='manual')
    backend = fields.Selection([])
    logs = fields.Text(string='Logs')  # If we have a better idea for logs...
    login = fields.Char()
    password = fields.Char(
        help="If you don't want to store the password in Odoo's database, "
        "leave this field empty and you will get a wizard to ask you the "
        "password on every download.")
    # fields for method = 'auto'
    next_run = fields.Date(string='Next Download Date')
    interval_type = fields.Selection([
        ('days', 'Day(s)'),
        ('weeks', 'Week(s)'),
        ('months', 'Month(s)'),
        ('years', 'Year'),
        ], string='Download Frequency', default='months')
    interval_number = fields.Integer(string='Frequency', default=1)

    _sql_constraints = [(
        'interval_number_positive',
        'CHECK(interval_number > 0)',
        'The frequency must be strictly positive')]

    def credentials_stored(self):
        if self.login and self.password:
            return True
        return False

    def prepare_credentials(self):
        credentials = {
            'login': self.login,
            'password': self.password,
            }
        return credentials

    def download(self, credentials):
        '''Returns list of invoice IDs. Updates last_run'''
        self.last_run = fields.Date.context_today(self)
        return []

    def binary_invoice2invoice_id(self, binary_invoice, invoice_filename):
        invoice_id = False
        try:
            invoice_b64 = binary_invoice.encode('base64')
            vals = {
                'invoice_file': invoice_b64,
                'invoice_filename': invoice_filename,
            }
            wiz = self.env['account.invoice.import'].create(vals)
            parsed_inv = wiz.parse_invoice()
            wiz_action = wiz.create_invoice_action(parsed_inv)
            if isinstance(wiz_action, dict) and wiz_action.get('res_id'):
                invoice_id = wiz_action['res_id']
        except Exception as e:
            logger.warning('Error in invoice parsing. Error: %s', e)
        return invoice_id

    def run(self):
        self.ensure_one()
        iaao = self.env['ir.actions.act_window']
        logger.info('Start to run invoice download %s', self.name)
        if not self.backend:
            raise UserError(_(
                "No backend configured for download configuration "
                "'%s'.") % self.name)
        if self.credentials_stored():
            logger.info(
                'Credentials stored for %s, launching download', self.name)
            credentials = self.prepare_credentials()
            invoice_ids = self.download(credentials)
            self.last_run = fields.Date.context_today(self)
            if invoice_ids:
                action = iaao.for_xml_id(
                    'account', 'action_invoice_tree2')
                action.update({
                    'views': False,
                    'view_id': False,
                    'domain': "[('id', 'in', %s)]" % invoice_ids,
                })
                return action
            else:
                raise UserError(_('No invoice downloaded'))
                # Problem: it rolls-back the update of last_run...
        else:
            credentials_wiz_action = iaao.for_xml_id(
                'account_invoice_download',
                'account_invoice_download_credentials_action')
            return credentials_wiz_action
