# -*- coding: utf-8 -*-
# © 2015-2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Import Invoice2data',
    'version': '8.0.2.0.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Import supplier invoices using the invoice2data lib',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'http://www.akretion.com',
    'depends': ['account_invoice_import'],
    'external_dependencies': {'python': ['invoice2data']},
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/invoice2data_template.xml',
    ],
    'demo': ['demo/demo_data.xml'],
    'images': ['images/sshot-wizard1.png'],
    'installable': True,
}
