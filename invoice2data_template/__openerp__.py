# -*- coding: utf-8 -*-
# © 2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Templates for invoice2data",
    "version": "9.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "summary": "Store and edit templates in the database",
    "depends": [
        'account',
    ],
    "data": [
        "views/invoice2data_template.xml",
        "security/res_groups.xml",
        'security/ir.model.access.csv',
    ],
    "external_dependencies": {
        'python': ['invoice2data'],
    },
}
