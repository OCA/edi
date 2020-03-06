# -*- coding: utf-8 -*-
{
    'name': "Base EDI Exchange Holodeck",

    'summary': """
        Base Module for Exchange of EDI documents using holodeck server
        """,

    'description': """
Base EDI Exchange Holodeck
====================

* 
    """,

    'author': "Callino",
    'website': "http://callino.at",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '12.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base_edi_exchange'],

    # always loaded
    'data': [
        'views/base_edi_exchange.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}