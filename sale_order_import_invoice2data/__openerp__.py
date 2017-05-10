# -*- coding: utf-8 -*-
{
    'name': 'Sale Order PDF Import',
    'version': '8.0.1.0.0',
    'category': 'Sales Management',
    'license': 'AGPL-3',
    'summary': 'Import PDF sale order files',
    'author': 'Sunflower IT,Odoo Community Association (OCA)',
    'website': 'http://sunflowerweb.nl',
    'depends': [
        'sale_order_import',
        'document'
    ],
    'external_dependencies': {
        'python': [
            'invoice2data',
        ]
    },
    'installable': True,
}
