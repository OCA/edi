# -*- coding: utf-8 -*-
# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Factur-X',
    'version': '10.0.1.0.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Generate Factur-X/ZUGFeRD customer invoices',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'http://www.akretion.com',
    'depends': ['account_payment_partner', 'base_zugferd', 'base_vat'],
    'external_dependencies': {'python': ['facturx']},
    'data': [
        'views/res_partner.xml',
        'views/account_config_settings.xml',
        ],
    'installable': True,
}
