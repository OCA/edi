# -*- coding: utf-8 -*-
{
    'name': "Base EDI Exchange Stock",

    'summary': """
        Base Module for Exchange of EDI documents of type Stock
        """,

    'description': """
Base EDI Exchange Stock
=======================

* 
    """,

    'author': "Callino",
    'website': "http://callino.at",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '12.0',

    # any module necessary for this one to work correctly
    'depends': ['base_edi_exchange', 'stock_picking_import'],

    # always loaded
    'data': [
        'views/stock_picking.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}