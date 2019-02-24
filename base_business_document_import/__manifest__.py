# Copyright 2016-2019 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Base Business Document Import',
    'version': '12.0.1.0.0',
    'category': 'Tools',
    'license': 'AGPL-3',
    'summary': 'Provides technical tools to import sale orders or supplier '
    'invoices',
    'author': 'Akretion, Nicolas JEUDY, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi',
    'depends': [
        'base_vat_sanitized',
        'account_tax_unece',
        'uom_unece',
    ],
    'external_dependencies': {'python': ['PyPDF2']},
}
