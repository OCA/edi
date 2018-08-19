# -*- coding: utf-8 -*-
# Copyright 2018 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class WeboobParameter(models.Model):
    _name = 'weboob.parameter'
    _description = 'Additional parameters to configure a Weboob backend'

    download_config_id = fields.Many2one(
        'account.invoice.download.config', string='Invoice Download Config',
        ondelete='cascade')
    key = fields.Char(required=True)
    value = fields.Char()
    note = fields.Char(string='Help')
