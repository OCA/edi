# Copyright 2018 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.account_invoice_download_ovh.models.\
    account_invoice_download_config import ENDPOINTS
import logging
logger = logging.getLogger(__name__)

try:
    import ovh
except ImportError:
    logger.debug('Cannot import ovh')


class OvhApiCredentials(models.TransientModel):
    _name = 'ovh.api.credentials'
    _description = 'Generate OVH API credentials'

    download_config_id = fields.Many2one(
        'account.invoice.download.config', string="Download Config",
        readonly=True, required=True)
    endpoint = fields.Selection(
        ENDPOINTS, string='Endpoint', default='ovh-eu')
    application_key = fields.Char(string='Application Key')
    application_secret = fields.Char(string='Application Secret')
    application_url = fields.Char(string='Application URL', readonly=True)
    validation_url = fields.Char(string='Validation URL', readonly=True)
    consumer_key = fields.Char(string='Consumer Key', readonly=True)
    validation_url_ok = fields.Boolean(string='Validation URL Done')
    state = fields.Selection([
        ('step1', 'Step1'),
        ('step2', 'Step2'),
        ('step3', 'Step3'),
        ], string='State', readonly=True, default='step1')

    @api.model
    def default_get(self, fields_list):
        res = super(OvhApiCredentials, self).default_get(fields_list)
        assert self._context.get('active_model') ==\
            'account.invoice.download.config'
        download_config = self.env['account.invoice.download.config'].browse(
            self._context['active_id'])
        res['download_config_id'] = download_config.id
        if download_config.ovh_endpoint:
            res['endpoint'] = download_config.ovh_endpoint
        return res

    def action_continue_wizard(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id(
            'account_invoice_download_ovh', 'ovh_api_credentials_action')
        action['res_id'] = self.id
        return action

    def run_step1(self):
        self.ensure_one()
        assert self.endpoint
        endpoint2appurl = {
            'ovh-eu': 'https://eu.api.ovh.com/createApp/',
            'ovh-us': 'https://api.ovhcloud.com/createApp/',
            'ovh-ca': 'https://ca.api.ovh.com/createApp/',
            'soyoustart-eu': 'https://eu.api.soyoustart.com/createApp/',
            'soyoustart-ca': 'https://ca.api.soyoustart.com/createApp/',
            'kimsufi-eu': 'https://eu.api.kimsufi.com/createApp/',
            'kimsufi-ca': 'https://ca.api.kimsufi.com/createApp/',
            }
        self.write({
            'application_url': endpoint2appurl[self.endpoint],
            'state': 'step2',
            })
        return self.action_continue_wizard()

    def run_step2(self):
        self.ensure_one()
        if (
                not self.application_key or
                not self.application_secret or
                not self.endpoint):
            raise UserError(_(
                "The endpoint, the application key and the application secret "
                "must be set before validation."))
        client = ovh.Client(
            endpoint=self.endpoint,
            application_key=self.application_key,
            application_secret=self.application_secret)

        # Request RO, /me/bill* API access
        ck = client.new_consumer_key_request()
        ck.add_rules(ovh.API_READ_ONLY, "/me/bill*")

        # Request validation
        validation = ck.request()

        if not validation['validationUrl'] or not validation['consumerKey']:
            raise UserError(_(
                "The request to generate the consumer key failed."))

        self.write({
            'validation_url': validation['validationUrl'],
            'consumer_key': validation['consumerKey'],
            'state': 'step3',
            })
        return self.action_continue_wizard()

    def run_step3(self):
        self.ensure_one()
        if not self.validation_url_ok:
            raise UserError(_(
                "Go to the Validation URL, enter the required information and "
                "validate, then check the option to attest that you did it."))
        self.download_config_id.write({
            'ovh_endpoint': self.endpoint,
            'ovh_application_key': self.application_key.strip(),
            'ovh_application_secret': self.application_secret.strip(),
            'ovh_consumer_key': self.consumer_key.strip(),
            })
        return True
