# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountInvoiceImportConfig(models.Model):
    _inherit = 'account.invoice.import.config'

    download_config_ids = fields.One2many(
        'account.invoice.download.config', 'import_config_id',
        string='Download Configurations')
