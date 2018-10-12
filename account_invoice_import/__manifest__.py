# © 2015-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Import',
    'version': '11.0.1.0.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Import supplier invoices/refunds as PDF or XML files',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'http://www.akretion.com',
    'depends': [
        'account',
        'base_iban',
        'base_business_document_import',
        'onchange_helper',
        # add bank_payment dependency to have commercial_partner_id on invoice
        # PR in odoo will be create soon
        'account_payment_partner',
        ],
    'data': [
        'security/ir.model.access.csv',
        'security/rule.xml',
        'views/account_invoice_import_config.xml',
        'views/res_config_settings.xml',
        'wizard/account_invoice_import_view.xml',
        'views/account_invoice.xml',
        'views/partner.xml',
    ],
    'images': ['images/sshot-wizard1.png'],
    'installable': True,
}
