{
    'name': "Base EDI Exchange",

    'summary': """
        Base Module for Exchange of EDI documents
        """,
    'author': "Callino, Odoo Community Association (OCA)",
    'website': "http://callino.at",
    'development_status': "Beta",
    "license": "AGPL-3",
    'category': 'Accounting',
    'version': '12.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'account', 'purchase'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/base_edi_exchange.xml',
        'views/base_edi_transfer.xml',
        'views/res_partner.xml',
        'views/menu.xml',
        'data/ir_cron_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
