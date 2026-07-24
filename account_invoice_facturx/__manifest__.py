# Copyright 2017-2020 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Factur-X Invoices',
    'version': '11.0.0.0.0',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'summary': "module to generate Factur-X invoices",
    'author': 'Adaptation from Akretion,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/edi',
    'depends': [
        'account_e-invoice_generate',
        'account_payment_partner',
        'base_zugferd',
        'base_vat',
        ],
    'external_dependencies': {'python': ['facturx']},
    'data': [
        'views/res_partner.xml',
        'views/res_config_settings.xml',
        'views/report_invoice.xml',
    ],
    'post_init_hook': 'set_xml_format_in_pdf_invoice_to_facturx',
    'installable': True,
}
