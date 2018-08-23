# -*- coding: utf-8 -*-
# Copyright 2017-2018 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
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
    import_config_id = fields.Many2one(
        'account.invoice.import.config', string='Invoice Import Config',
        ondelete='cascade')
    partner_id = fields.Many2one(
        related='import_config_id.partner_id', readonly=True, store=True)
    last_run = fields.Date(
        string='Last Download Date',
        help="Date of the last successfull download")
    # Don't set last_run as readonly because sometimes we need to
    # manually fool the system
    backward_days = fields.Integer(
        string='Backward Days',
        help="By default, Odoo will download all invoices that are "
        "after the last download date. But it may happen that invoices "
        "are available online for download several days after their "
        "generation. So, if you set this parameter to 5, Odoo will "
        "download all invoices that are after the last download date "
        "minus 5 days.")
    download_start_date = fields.Date(
        compute='_compute_download_start_date', string='Download Start Date',
        readonly=True, store=True)
    method = fields.Selection([
        ('manual', 'Manual'),
        ('auto', 'Automatic'),
        ], string='Download Method', required=True, default='manual')
    backend = fields.Selection([])
    log_ids = fields.One2many(
        'account.invoice.download.log', 'download_config_id',
        string='Logs', readonly=True)
    login = fields.Char()
    password = fields.Char(
        help="If you don't want to store the password in Odoo's database, "
        "leave this field empty and you will get a wizard to ask you the "
        "password on every download.")
    # fields for method = 'auto'
    next_run = fields.Date(string='Next Download Date')
    # Don't set next_run as readonly because sometimes we need to
    # manually fool the system
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
        'The frequency must be strictly positive'), (
        'backward_days_positive',
        'CHECK(backward_days >= 0)',
        'The backward days must be positive')]

    @api.depends('backward_days', 'last_run')
    def _compute_download_start_date(self):
        for config in self:
            start_date = False
            if config.last_run:
                start_date = config.last_run
                if config.backward_days:
                    start_date_dt = fields.Date.from_string(config.last_run) -\
                        relativedelta(days=config.backward_days)
                    start_date = fields.Date.to_string(start_date_dt)
            config.download_start_date = start_date

    @api.depends('name', 'backend', 'method')
    def name_get(self):
        res = []
        for rec in self:
            name = u'%s (%s / %s)' % (rec.name, rec.backend, rec.method)
            res.append((rec.id, name))
        return res

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

    def download(self, credentials, logs):
        '''Returns a list of either:
            - pivot dict (example: ovh backend)
            - tuple: (invoice_file_b64, invoice_filename) (example: weboob).
        This method is inherited in backend-specific modules
        '''
        return []

    def run_button(self):
        self.ensure_one()
        iaao = self.env['ir.actions.act_window']
        if not self.backend:
            raise UserError(_(
                "No backend configured for download configuration "
                "'%s'.") % self.name)
        if not self.import_config_id:
            raise UserError(_(
                "No invoice import configuration for download configuration "
                "'%s'.") % self.name)
        if self.credentials_stored():
            logger.info(
                'Credentials stored for %s, launching download', self.name)
            credentials = self.prepare_credentials()
            invoice_ids, log_id = self.run(credentials)
            if invoice_ids:
                action = iaao.for_xml_id(
                    'account', 'action_invoice_tree2')
                action.update({
                    'views': False,
                    'view_id': False,
                    'domain': "[('id', 'in', %s)]" % invoice_ids,
                })
            else:
                action = iaao.for_xml_id(
                    'account_invoice_download',
                    'account_invoice_download_log_action')
                action.update({
                    'res_id': log_id,
                    'view_mode': 'form,tree',
                    'views': False,
                    })
            return action
        else:
            credentials_wiz_action = iaao.for_xml_id(
                'account_invoice_download',
                'account_invoice_download_credentials_action')
            return credentials_wiz_action

    def run(self, credentials):
        '''Do the real work. Handle try/except.
        Create log. Return list of invoices and log'''
        self.ensure_one()
        aio = self.env['account.invoice']
        aiio = self.env['account.invoice.import']
        logger.info(
            'Start to run invoice download %s (%s)',
            self.name, self.backend)
        if not self.backend:
            logger.error('Missing backend on invoice download %s', self.name)
            return ([], False)
        if not self.import_config_id:
            logger.error(
                'Missing invoice import config on invoice download %s',
                self.name)
            return ([], False)
        logs = {
            'msg': [],
            'result': 'success',
            }
        invoice_ids = []
        invoices_dl = []
        try:
            invoices_dl = self.download(credentials, logs)
        except Exception as e:
            logger.error('Failed to download invoice. Error: %s', e)
            logs['msg'].append(_('Failed to download invoice. Error: %s.') % e)
            logs['result'] = 'failure'
        company_id = self.company_id.id
        assert self.import_config_id.company_id.id == company_id
        import_config = self.import_config_id.convert_to_import_config()
        existing_refs = {}  # key = invoice reference, value = inv ID
        existing_invs = aio.search_read([
            ('type', 'in', ('in_invoice', 'in_refund')),
            ('commercial_partner_id', '=', self.partner_id.id),
            ('company_id', '=', company_id),
            ('reference', '!=', False)],
            ['reference'])
        for existing_inv in existing_invs:
            existing_refs[existing_inv.get('reference')] = existing_inv['id']
        logger.debug('existing_refs=%s', existing_refs)
        for inv_struc in invoices_dl:
            if isinstance(inv_struc, dict):  # Pivot format
                parsed_inv = inv_struc
            elif isinstance(inv_struc, tuple):
                invoice_file_b64, filename = inv_struc
                parsed_inv = aiio.parse_invoice(invoice_file_b64, filename)
            else:
                logger.error(
                    'Technical error that should never happen: '
                    'inv_struc is a %s', type(inv_struc))
                continue
            # Get partner from invoice import config, not from invoice
            parsed_inv['partner'] = {'recordset': self.partner_id}
            if (
                    parsed_inv.get('invoice_number') and
                    parsed_inv['invoice_number'] in existing_refs):
                logger.info(
                    'Skipping invoice %s dated %s because it already exists '
                    'in Odoo (ID %d)',
                    parsed_inv['invoice_number'], parsed_inv.get('date'),
                    existing_refs[parsed_inv['invoice_number']])
                logs['msg'].append(_(
                    'Skipping invoice %s dated %s because it already exists '
                    'in Odoo (ID %d).') % (
                    parsed_inv['invoice_number'], parsed_inv.get('date'),
                    existing_refs[parsed_inv['invoice_number']]))
                continue
            try:
                invoice = aiio.with_context(
                    force_company=company_id).create_invoice(
                        parsed_inv, import_config)
            except Exception as e:
                logs['msg'].append(_(
                    'Failed to create invoice. Error: %s. (parsed_inv=%s '
                    'import_config=%s)') % (e, parsed_inv, import_config))
                logs['result'] = 'failure'
                continue
            invoice_ids.append(invoice.id)
            logs['msg'].append(_(
                'Invoice number %s dated %s created (ID %d).') % (
                parsed_inv.get('invoice_number', 'none'),
                parsed_inv.get('date', 'none'), invoice.id))
        if logs['result'] == 'success':
            self.last_run = fields.Date.context_today(self)
        if not invoice_ids and logs['result'] == 'success':
            logs['msg'].append(_('No invoice downloaded.'))
        log = self.env['account.invoice.download.log'].create({
            'download_config_id': self.id,
            'message': '\n'.join(logs['msg']),
            'invoice_count': len(invoice_ids),
            'result': logs['result'],
            })
        logger.info(
            'End of invoice download %s (%s). IDs of created invoices: %s',
            self.name, self.backend, invoice_ids)
        return (invoice_ids, log.id)

    @api.model
    def run_cron(self):
        logger.info(
            'Start cron that auto-download supplier invoices with '
            'user %s ID %d', self.env.user.name, self.env.user.id)
        today_str = fields.Date.context_today(self)
        today_dt = fields.Date.from_string(today_str)
        configs = self.search([
            ('next_run', '<=', today_str),
            ('method', '=', 'auto'),
            ])
        for config in configs:
            if config.credentials_stored():
                credentials = config.prepare_credentials()
                config.run(credentials)
                int_number = config.interval_number
                int_type = config.interval_type
                config.next_run = today_dt + relativedelta(
                    days=int_type == 'days' and int_number or 0,
                    weeks=int_type == 'weeks' and int_number or 0,
                    months=int_type == 'months' and int_number or 0,
                    years=int_type == 'years' and int_number or 0,
                    )
            else:
                logger.warning(
                    'Cannot run download config %s because of missing '
                    'credentials', config.display_name)
        logger.info('End of the cron that auto-download supplier invoices')
