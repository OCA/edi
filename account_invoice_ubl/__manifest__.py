# Copyright 2016-2018 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice UBL',
    'version': '11.0.1.0.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Generate UBL XML file for customer invoices/refunds',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi/',
    'depends': [
        'account_e-invoice_generate',
        'account_payment_partner',
        'base_ubl_payment',
        ],
    'data': [
        'views/account_invoice.xml',
        'views/res_config_settings.xml',
        ],
    'post_init_hook': 'set_xml_format_in_pdf_invoice_to_ubl',
    'installable': True,
}
