# -*- coding: utf-8 -*-
{
    'name': "Base EDI Exchange Account Invoice",

    'summary': """
        Base Module for Exchange of EDI documents of type Invoice
        """,

    'description': """
Base EDI Exchange Account Invoice
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
    'depends': ['base_edi_exchange', 'account_invoice_import'],

    # always loaded
    'data': [
        'views/account_invoice.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}