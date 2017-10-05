# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
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
    weboob_module = fields.Selection('_get_weboob_modules')
    # TODO : add obj for additional params

    def download(self, credentials):
        if self.backend == 'weboob':
            return self.weboob_download(credentials)
        return super(AccountInvoiceDownloadConfig, self).download(credentials)

    def weboob_download(self, credentials):
        logger.info('START weboob operations')
        w = Weboob()
        invoice_ids = []
        back = w.build_backend(
            self.weboob_module, params=credentials, name='odoo')

        sub = back.iter_subscription().next()

        bills = back.iter_bills(sub)
        last_run = self.last_run
        invoice_ids = []
        for bill in bills:
            logger.debug('bill.id=%s, bill.fullid=%s', bill.id, bill.fullid)
            inv_details = bill.to_dict()
            logger.debug('bill.to_dict=%s', inv_details)
            logger.info("Found invoice dated %s", inv_details.get('date'))
            if (
                    last_run and
                    inv_details.get('date') and
                    fields.Date.to_string(inv_details['date']) < last_run):
                logger.info(
                    'Skipping invoice %s dated %s dated before last_run %s',
                    inv_details.get('label'), inv_details['date'], last_run)
                continue

            logger.info('Start to download bill with full ID %s', bill.fullid)
            pdf_inv = back.download_document(bill.id)
            filename = 'invoice_%s_%s.pdf' % (
                self.weboob_module, inv_details.get('label'))
            invoice_id = self.binary_invoice2invoice_id(pdf_inv, filename)
            if invoice_id:
                invoice_ids.append(invoice_id)
        return invoice_ids
