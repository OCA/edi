# Copyright 2015-2020 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Import Invoice2data',
    'version': '12.0.1.0.0',
    'category': 'Invoicing Management',
    'license': 'AGPL-3',
    'summary': 'Import supplier invoices using the invoice2data lib',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi',
    'depends': ['account_invoice_import'],
    'external_dependencies': {'python': ['invoice2data']},
    'data': ['wizard/account_invoice_import_view.xml'],
    'demo': ['demo/demo_data.xml'],
    'installable': True,
}
