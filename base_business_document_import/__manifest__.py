# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Base Business Document Import',
    'version': '11.0.1.0.1',
    'category': 'Tools',
    'license': 'AGPL-3',
    'summary': 'Provides technical tools to import sale orders or supplier '
    'invoices',
    'author': 'Akretion, Nicolas JEUDY, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi',
    'depends': [
        'base_vat_sanitized',
        'account_tax_unece',
        'product_uom_unece',
    ],
    'external_dependencies': {'python': ['PyPDF2']},
}
