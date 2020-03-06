# -*- coding: utf-8 -*-
{
    'name': "Base EDI Exchange Sale",

    'summary': """
        Base Module for Exchange of EDI documents of type Sale
        """,

    'description': """
Base EDI Exchange Sale
====================

* 
    """,

    'author': "Callino",
    'website': "http://callino.at",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '10.0',

    # any module necessary for this one to work correctly
    'depends': ['base_edi_exchange', 'sale_order_import'],

    # always loaded
    'data': [
        'views/sale_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}