# © 2015-2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Download OVH',
    'version': '12.0.1.0.1',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': 'Get OVH Invoice via the API',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi',
    'depends': ['account_invoice_download'],
    'external_dependencies': {'python': ['requests', 'ovh']},
    'data': [
        'wizard/ovh_api_credentials_view.xml',
        'views/account_invoice_download_config.xml',
    ],
    'demo': ['demo/ovh_demo.xml'],
    'installable': True,
    'application': True,
}
