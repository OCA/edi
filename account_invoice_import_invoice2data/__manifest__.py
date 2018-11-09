# Copyright 2015-2016 Akretion
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Import Invoice2data',
    'version': '11.0.1.0.0',
    'development_status': "Production/Stable",
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Import supplier invoices using the invoice2data lib',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi',
    'depends': ['account_invoice_import'],
    'external_dependencies': {'python': ['pdftotext', 'invoice2data']},
    'data': ['wizard/account_invoice_import_view.xml'],
    'demo': ['demo/demo_data.xml'],
    'images': ['images/sshot-wizard1.png'],
    'installable': True,
}
