# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

logger = logging.getLogger(__name__)


class AccountInvoiceDownloadCredentials(models.TransientModel):
    _name = 'account.invoice.download.credentials'
    _description = 'Wizard to ask credentials to download invoice'

    download_config_id = fields.Many2one(
        'account.invoice.download.config', 'Invoice Download Config',
        required=True)
    backend = fields.Selection(
        related='download_config_id.backend', readonly=True)
    login = fields.Char()
    password = fields.Char()
    invoice_ids = fields.Char(
        help='This field is a technical hack to be able to return '
        'the action with the created invoices')

    @api.model
    def default_get(self, fields_list):
        res = super(AccountInvoiceDownloadCredentials, self).default_get(
            fields_list)
        assert self._context.get('active_model') ==\
            'account.invoice.download.config', 'Wrong active_model'
        assert self._context.get('active_id'), 'Missing active_id'
        config = self.env['account.invoice.download.config'].browse(
            self._context['active_id'])
        res.update({
            'download_config_id': config.id,
            'login': config.login,
            })
        return res

    @api.model
    def prepare_and_remove_credentials(self, vals):
        credentials = {
            'login': vals.get('login'),
            'password': vals.get('password'),
            }
        # NEVER store password in Odoo's database !
        if 'password' in vals:
            vals.pop('password')
        return credentials

    @api.model
    def create(self, vals):
        credentials = self.prepare_and_remove_credentials(vals)
        if not vals.get('download_config_id'):
            raise UserError(_('Missing Invoice Download Config'))
        download_config = self.env['account.invoice.download.config'].browse(
            vals['download_config_id'])
        invoice_ids = download_config.download(credentials)
        download_config.last_run = fields.Date.context_today(self)
        vals['invoice_ids'] = invoice_ids
        return super(AccountInvoiceDownloadCredentials, self).create(vals)

    def run(self):
        """We don't do anything here because everything is done in create()"""
        self.ensure_one()
        # TODO: find a way to return an action with the downloaded invoices
        # will probably need a Char field on the wizard set by create
        if self.invoice_ids:
            action = self.env['ir.actions.act_window'].for_xml_id(
                'account', 'action_invoice_tree2')
            action.update({
                'views': False,
                'view_id': False,
                'domain': "[('id', 'in', %s)]" % self.invoice_ids,
                })
            return action
        else:
            raise UserError(_("No invoice downloaded"))
