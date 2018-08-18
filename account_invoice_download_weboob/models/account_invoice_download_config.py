# -*- coding: utf-8 -*-
# Copyright 2017-2018 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import logging

logger = logging.getLogger(__name__)
try:
    from weboob.core import Weboob
except ImportError:
    logger.debug('Cannot import weboob')


class AccountInvoiceDownloadConfig(models.Model):
    _inherit = 'account.invoice.download.config'

    @api.model
    def _get_weboob_modules(self):
        w = Weboob()
        res = []
        weboob_modules = w.repositories.get_all_modules_info('CapDocument')
        for name, info in weboob_modules.iteritems():
            res.append((name, info.description))
        return res

    backend = fields.Selection(
        selection_add=[('weboob', 'Weboob')])
    weboob_module = fields.Selection(
        '_get_weboob_modules', string='Weboob Module')
    # TODO : add obj for additional params

    def download(self, credentials):
        if self.backend == 'weboob':
            return self.weboob_download(credentials)
        return super(AccountInvoiceDownloadConfig, self).download(credentials)

    def weboob_download(self, credentials):
        logger.info(
            'Start weboob operations with module %s', self.weboob_module)
        w = Weboob()
        back = w.build_backend(
            self.weboob_module, params=credentials, name='odoo')

        sub = back.iter_subscription().next()

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
                self.weboob_module,
                inv_details.get('label') and
                inv_details['label'].replace(' ', '_'),
                inv_details.get('format', 'pdf'))
            invoices.append((pdf_inv.encode('base64'), filename))
        return invoices
