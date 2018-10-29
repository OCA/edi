# © 2015-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Import Facturae',
    'version': '11.0.1.0.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Import supplier invoices/refunds in facturae syntaxis',
    'author': 'Akretion, Nicolas JEUDY, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi',
    'depends': [
        'account_invoice_import',
        'base_iso3166'
    ],
    'data': [
    ],
    'external_dependencies': {
        'python': [
            'xmlsig',
        ]
    },
    'images': ['images/sshot-wizard1.png'],
    'installable': True,
}
