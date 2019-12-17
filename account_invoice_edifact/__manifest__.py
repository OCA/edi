# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Account Invoice Edifact',
    "summary": "Generate edifact files for customer invoices/refunds",
    'version': '12.0.1.0.1',
    "development_status": "Production/Stable",
    'category': 'Accounting & Finance',
    'author': "PlanetaTIC,Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': 'https://github.com/OCA/edi',
    'depends': [
        'account',
        'base_edifact',
    ],
    'demo': [],
    'data': [
        'views/account_invoice_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
