# -*- coding: utf-8 -*-
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Sale Order Import Edifact',
    "summary": "Import sale orders using files in Edifact protocol",
    'version': '12.0.1.0.1',
    "development_status": "Production/Stable",
    "category": "Sales Management",
    'author': "PlanetaTIC,Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': 'https://github.com/OCA/edi',
    'depends': [
        'sale_order_import',
        'base_edifact',
    ],
    'demo': [],
    'data': [
        'views/partner_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
