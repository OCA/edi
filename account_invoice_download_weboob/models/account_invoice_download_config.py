# -*- coding: utf-8 -*-
# Copyright 2017-2018 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import logging

logger = logging.getLogger(__name__)
try:
    from weboob.core import Weboob
    from weboob.exceptions import BrowserIncorrectPassword
except ImportError:
    logger.debug('Cannot import weboob')


class AccountInvoiceDownloadConfig(models.Model):
    _inherit = 'account.invoice.download.config'

    backend = fields.Selection(
        selection_add=[('weboob', 'Weboob')])
    weboob_module_id = fields.Many2one(
        'weboob.module', string='Weboob Module', ondelete='restrict',
        domain=[('state', '=', 'installed')])
    weboob_has_parameter = fields.Boolean(
        related='weboob_module_id.has_parameters', readonly=True)
    weboob_parameter_ids = fields.One2many(
        'weboob.parameter', 'download_config_id',
        string='Weboob Additional Parameters')

    @api.onchange('weboob_module_id')
    def weboob_module_id_change(self):
        if self.weboob_module_id and self.weboob_module_id.has_parameters:
            w = Weboob()
            bmod = w.modules_loader.get_or_load_module(
                self.weboob_module_id.name)
            new_params = self.env['weboob.parameter']
            for key, value in bmod.config.iteritems():
                if key not in ['login', 'password']:
                    note = value.label or ''
                    if value.choices:
                        options = ', '.join([
                            "'%s' (%s)" % (key_opt, help_opt)
                            for (key_opt, help_opt) in value.choices.items()])
                        note = _("%s. Possible values: %s.") % (note, options)
                    param = new_params.new({
                        'key': key,
                        'note': note,
                        })
                    new_params += param
            self.weboob_parameter_ids = new_params

    def prepare_credentials(self):
        credentials = super(
            AccountInvoiceDownloadConfig, self).prepare_credentials()
        if self.backend == 'weboob' and self.weboob_parameter_ids:
            for param in self.weboob_parameter_ids:
                if param.key and param.value:
                    credentials[param.key.strip()] = param.value.strip()
        return credentials

    def download(self, credentials, logs):
        if self.backend == 'weboob':
            return self.weboob_download(credentials, logs)
        return super(AccountInvoiceDownloadConfig, self).download(
            credentials, logs)

    def weboob_download(self, credentials, logs):
        logger.info(
            'Start weboob operations with module %s',
            self.weboob_module_id.name)
        w = Weboob()
        back = w.build_backend(
            self.weboob_module_id.name, params=credentials, name='odoo')

        try:
            sub = back.iter_subscription().next()
        except BrowserIncorrectPassword:
            logs['msg'].append(_('Wrong password.'))
            logs['result'] = 'failure'
            return []

        bills = back.iter_bills(sub)
        start_date = self.download_start_date
        invoices = []
        for bill in bills:
            logger.debug('bill.id=%s, bill.fullid=%s', bill.id, bill.fullid)
            inv_details = bill.to_dict()
            logger.info('bill.to_dict=%s', inv_details)
            # bill.to_dict=OrderedDict([
            # ('id', u'60006530609_216421161'),
            # ('url', u'https://api.bouyguestelecom.fr/comptes-facturat...'),
            # ('date', date(2018, 7, 16)),
            # ('format', u'pdf'),
            # ('label', u'Juillet 2018'),
            # ('type', u'bill'),
            # ('transactions', []),
            # ('price', Decimal('30.99')),
            # ('currency', u'EUR'),
            # ('vat', NotLoaded),
            # ('duedate', NotLoaded), ('startdate', NotLoaded),
            # ('finishdate', NotLoaded), ('income', False)])
            # Do we have invoice number here ? NO
            logger.info("Found invoice dated %s", inv_details.get('date'))
            if (
                    start_date and
                    inv_details.get('date') and
                    fields.Date.to_string(inv_details['date']) < start_date):
                logger.info(
                    'Skipping invoice %s dated %s dated before '
                    'download_start_date %s',
                    inv_details.get('label'), inv_details['date'], start_date)
                continue

            logger.info('Start to download bill with full ID %s', bill.fullid)
            pdf_inv = back.download_document(bill.id)
            filename = 'invoice_%s_%s.%s' % (
                self.weboob_module_id.name,
                inv_details.get('label') and
                inv_details['label'].replace(' ', '_'),
                inv_details.get('format', 'pdf'))
            invoices.append((pdf_inv.encode('base64'), filename))
        return invoices
