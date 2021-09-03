# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice Download OVH",
    "version": "14.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Get OVH Invoice via the API",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/edi",
    "depends": ["account_invoice_download"],
    "external_dependencies": {"python": ["requests", "ovh"]},
    "data": [
        "wizard/ovh_api_credentials_view.xml",
        "views/account_invoice_download_config.xml",
        "security/ir.model.access.csv",
    ],
    "demo": ["demo/ovh_demo.xml"],
    "installable": True,
    "application": True,
}
