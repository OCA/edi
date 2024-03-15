# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice UBL Email Attachment',
    'summary': 'Automatically adds the UBL file to the email.',
    'version': '12.0.1.0.1',
    'category': 'Accounting & Finance',
    'author': 'Onestein, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi',
    'license': 'AGPL-3',
    'depends': [
        'account_invoice_ubl'
    ],
    'data': [
        'views/res_config_settings.xml',
    ],
    'installable': True,
}
