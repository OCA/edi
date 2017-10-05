# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Download',
    'version': '10.0.1.0.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Auto-download supplier invoices and import them',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'http://www.akretion.com',
    'depends': [
        'account_invoice_import',
        ],
    'data': [
        'security/rule.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_download_config.xml',
        'wizard/account_invoice_download_credentials_view.xml',
    ],
    'installable': True,
}
