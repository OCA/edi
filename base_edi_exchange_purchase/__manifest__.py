# -*- coding: utf-8 -*-
{
    'name': "Base EDI Exchange Purchase",

    'summary': """
        Base Module for Exchange of EDI documents of type Purchase
        """,

    'description': """
Base EDI Exchange Purchase
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
    'depends': ['base_edi_exchange', 'purchase_order_import', 'base_edi_exchange_sale'],

    # always loaded
    'data': [
        'views/purchase.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}