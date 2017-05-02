# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sale Order Import',
    'version': '9.0.1.0.0',
    'category': 'Sales Management',
    'license': 'AGPL-3',
    'summary': 'Import RFQ or sale orders from files',
    'author': 'Akretion,Odoo Community Association (OCA), Sunflower IT',
    'website': 'http://www.akretion.com',
    'depends': ['sale'],
    'depends': ['sale_commercial_partner', 'base_business_document_import'],
    'data': [
        'wizard/sale_order_import_view.xml',
    ],
    'installable': True,
}
