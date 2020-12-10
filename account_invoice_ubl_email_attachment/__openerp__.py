# -*- coding: utf-8 -*
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice UBL Email Attachment',
    'summary': 'Automatically adds the UBL file to the email.',
    'version': '8.0.1.0.0',
    'category': 'Accounting & Finance',
    'author': 'Onestein, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi/',
    'license': 'AGPL-3',
    'depends': [
        'account_invoice_ubl',
        'email_template',
    ],
    'data': [
        'views/res_company.xml',
    ],
    'installable': True,
}
