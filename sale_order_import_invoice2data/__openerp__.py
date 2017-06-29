# -*- coding: utf-8 -*-
{
    'name': 'Sale Order PDF Import',
    'version': '9.0.1.0.0',
    'category': 'Sales Management',
    'license': 'AGPL-3',
    'summary': 'Import PDF sale order files',
    'author': 'Sunflower IT,Therp BV,Odoo Community Association (OCA)',
    'website': 'http://sunflowerweb.nl',
    'depends': [
        'sale_order_import',
        'document',
        'invoice2data_template',
    ],
    'demo': [
        'demo/invoice2data_template.xml',
    ],
    'installable': True,
}
