# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# © 2017-Today Serpent Consulting Services Pvt. Ltd.
#   (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Base Business Document Import Phone',
    'version': '9.0.1.0.0',
    'category': 'Hidden',
    'license': 'AGPL-3',
    'summary': 'Use phone numbers to match partners upon import of '
               'business documents',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'http://www.akretion.com',
    'depends': [
        'base_phone',
        'base_business_document_import',
        ],
    'installable': True,
    'auto_install': True,
}
