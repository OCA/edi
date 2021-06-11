# Copyright 2015-2018 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
from odoo.exceptions import UserError
import json
import requests
import logging
import base64

logger = logging.getLogger(__name__)

try:
    import ovh
except ImportError:
    logger.debug('Cannot import ovh')

ENDPOINTS = [
    ('ovh-eu', 'OVH Europe API'),
    ('ovh-us', 'OVH US API'),
    ('ovh-ca', 'OVH North-America API'),
    ('soyoustart-eu', 'So you Start Europe API'),
    ('soyoustart-ca', 'So you Start North America API'),
    ('kimsufi-eu', 'Kimsufi Europe API'),
    ('kimsufi-ca', 'Kimsufi North America API'),
    # ('runabove-ca', 'RunAbove API'),
    ]


class AccountInvoiceDownloadConfig(models.Model):
    _inherit = 'account.invoice.download.config'

    backend = fields.Selection(
        selection_add=[('ovh', 'OVH')])
    ovh_endpoint = fields.Selection(
        ENDPOINTS, string='OVH Endpoint', default='ovh-eu')
    ovh_application_key = fields.Char(string='OVH Application Key')
    ovh_application_secret = fields.Char(
        string='OVH Application Secret')
    ovh_consumer_key = fields.Char(string='OVH Consumer Key')

    def prepare_credentials(self):
        credentials = super(
            AccountInvoiceDownloadConfig, self).prepare_credentials()
        if self.backend == 'ovh':
            credentials = {
                'endpoint': self.ovh_endpoint,
                'application_key': self.ovh_application_key,
                'application_secret': self.ovh_application_secret,
                'consumer_key': self.ovh_consumer_key,
                }
        return credentials

    def credentials_stored(self):
        if self.backend == 'ovh':
            if (
                    self.ovh_endpoint and
                    self.ovh_application_key and
                    self.ovh_application_secret and
                    self.ovh_consumer_key):
                return True
            else:
                raise UserError(_("You must set all the OVH parameters."))
        return super(AccountInvoiceDownloadConfig, self).credentials_stored()

    def download(self, credentials, logs):
        if self.backend == 'ovh':
            return self.ovh_download(credentials, logs)
        return super(AccountInvoiceDownloadConfig, self).download(
            credentials, logs)

    def ovh_invoice_attach_pdf(self, parsed_inv, pdf_invoice_url):
        logger.info(
            'Starting to download PDF of OVH invoice %s dated %s',
            parsed_inv['invoice_number'], parsed_inv['date'])
        logger.debug('OVH invoice download url: %s', pdf_invoice_url)
        rpdf = requests.get(pdf_invoice_url)
        logger.info(
            'OVH invoice PDF download HTTP code: %s', rpdf.status_code)
        if rpdf.status_code == 200:
            res = base64.encodestring(rpdf.content)
            logger.info(
                'Successfull download of the PDF of the OVH invoice %s',
                parsed_inv['invoice_number'])
            filename = 'OVH_invoice_%s.pdf' % parsed_inv['invoice_number']
            parsed_inv['attachments'] = {filename: res}
        else:
            logger.warning(
                'Could not download the PDF of the OVH invoice %s. HTTP '
                'error %d', parsed_inv['invoice_number'], rpdf.status_code)
        return

    def ovh_download(self, credentials, logs):
        invoices = []
        logger.info(
            'Start to download OVH invoices with config %s and endpoint %s',
            self.name, self.ovh_endpoint)
        try:
            client = ovh.Client(
                endpoint=self.ovh_endpoint,
                application_key=self.ovh_application_key,
                application_secret=self.ovh_application_secret,
                consumer_key=self.ovh_consumer_key)
        except Exception as e:
            logs['msg'].append(_(
                "Cannot connect to the OVH API with endpoint '%s'. "
                "The error message is: '%s'.") % (
                    self.ovh_endpoint, str(e)))
            logs['result'] = 'failure'
            return []
        logger.info(
            'Starting OVH API query /me/bill (d/l config %s)', self.name)
        params = {}
        if self.download_start_date:
            params = {'date.from': self.download_start_date}
        res_ilist = client.get('/me/bill', **params)
        logger.debug(
            'Result of /me/bill : %s', json.dumps(res_ilist, indent=4))

        for oinv_num in res_ilist:
            logger.info(
                'Starting OVH API query /me/bill/%s (d/l config %s)',
                oinv_num, self.name)
            res_inv = client.get('/me/bill/%s' % oinv_num)
            logger.debug(
                'Result of /me/bill/%s : %s',
                oinv_num, json.dumps(res_inv))
            oinv_date = res_inv['date'][:10]
            if (
                    not res_inv['priceWithoutTax'].get('value') and
                    not res_inv['priceWithTax'].get('value')):
                logs['msg'].append(_(
                    'Skipping OVH invoice %s dated %s because '
                    'the amount is 0') % (oinv_num, oinv_date))
                continue
            if oinv_num and oinv_num.startswith('PP_'):
                logs['msg'].append(_(
                    'Skipping OVH invoice %s dated %s because it is a '
                    'special pre-paid invoice') % (oinv_num, oinv_date))
                continue

            currency_code = res_inv['priceWithoutTax']['currencyCode']
            parsed_inv = {
                'invoice_number': oinv_num,
                'currency': {'iso': currency_code},
                'date': oinv_date,
                'amount_untaxed': res_inv['priceWithoutTax'].get('value'),
                'amount_total': res_inv['priceWithTax'].get('value'),
            }
            self.ovh_invoice_attach_pdf(parsed_inv, res_inv['pdfUrl'])

            if self.import_config_id.invoice_line_method.startswith('nline'):
                parsed_inv['lines'] = []
                logger.info(
                    'Starting OVH API query /me/bill/%s/details '
                    'invoice number %s dated %s',
                    oinv_num, parsed_inv['invoice_number'], parsed_inv['date'])
                res_ilines = client.get('/me/bill/%s/details' % oinv_num)
                logger.debug(
                    'Result /me/bill/%s/details: %s',
                    oinv_num, json.dumps(res_ilines))
                for line in res_ilines:
                    logger.info(
                        'Starting OVH API query /me/bill/%s/details/%s '
                        'invoice number %s dated %s',
                        oinv_num, line,
                        parsed_inv['invoice_number'], parsed_inv['date'])
                    res_iline = client.get(
                        '/me/bill/%s/details/%s' % (oinv_num, line))
                    logger.debug(
                        'Result /me/bill/%s/details/%s: %s',
                        oinv_num, line, json.dumps(res_iline))
                    line = {
                        # We don't have accurate product code in the OVH API
                        # We had a product code in the SoAPI...
                        # 'product': {'code': 'xxx'},
                        'name': res_iline['description'],
                        'qty': int(res_iline['quantity']),
                        'price_unit': res_iline['unitPrice']['value'],
                        'uom': {'unece_code': 'C62'},
                        'taxes': [{
                            'amount_type': 'percent',
                            'amount': 20.0,
                            'unece_type_code': 'VAT',
                            'unece_categ_code': 'S',
                            }]
                        }
                    if res_iline['periodStart'] and res_iline['periodEnd']:
                        line.update({
                            'date_start': res_iline['periodStart'],
                            'date_end': res_iline['periodEnd']
                            })
                    parsed_inv['lines'].append(line)

            logger.debug('Final parsed_inv=%s', parsed_inv)
            invoices.append(parsed_inv)

        return invoices
