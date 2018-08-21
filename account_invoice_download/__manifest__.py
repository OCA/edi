# -*- coding: utf-8 -*-
# Copyright 2017-2018 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Download',
    'version': '10.0.1.0.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': 'Auto-download supplier invoices and import them',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi',
    'depends': [
        'account_invoice_import',
        ],
    'data': [
        'security/rule.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_download_config.xml',
        'views/account_invoice_download_log.xml',
        'views/account_invoice_import_config.xml',
        'wizard/account_invoice_download_credentials_view.xml',
        'data/cron.xml',
    ],
    'installable': True,
}
