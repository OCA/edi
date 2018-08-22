# -*- coding: utf-8 -*-
# © 2015-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Import Factur-X',
    'version': '10.0.1.0.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Import ZUGFeRD and Factur-X supplier invoices/refunds',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'http://www.akretion.com',
    'depends': ['account_invoice_import', 'base_zugferd'],
    'external_dependencies': {'python': ['facturx']},
    'data': ['wizard/account_invoice_import_view.xml'],
    'demo': ['demo/demo_data.xml'],
    'installable': True,
}
