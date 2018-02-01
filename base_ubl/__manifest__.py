# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Base UBL',
    'version': '11.0.1.0.0',
    'category': 'Hidden',
    'license': 'AGPL-3',
    'summary': 'Base module for Universal Business Language (UBL)',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'https://github.com/oca/edi/',
    'depends': [
        'product_uom_unece',
        'account_tax_unece',
        'base_vat_sanitized',
        ],
    'external_dependencies': {'python': ['PyPDF2']},
    'installable': True,
}
