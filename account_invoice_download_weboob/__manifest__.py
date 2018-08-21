# -*- coding: utf-8 -*-
# Copyright 2017-2018 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Download Weboob',
    'version': '10.0.1.0.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': 'Auto-download supplier invoices with Weboob',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi',
    'depends': [
        'account_invoice_download',
        ],
    'external_dependencies': {'python': ['weboob']},
    'data': [
        'views/account_invoice_download_config.xml',
        'views/weboob_module.xml',
        'wizard/weboob_module_update_view.xml',
        'security/ir.model.access.csv',
    ],
    'post_init_hook': 'initial_update_module_list',
    'installable': True,
    'application': True,
}
