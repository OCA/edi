# Copyright 2023 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice Download Scaleway",
    "version": "14.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Get Scaleway Invoices via the API",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/edi",
    "depends": ["account_invoice_download"],
    "data": [
        "views/account_invoice_download_config.xml",
    ],
    "demo": ["demo/scaleway.xml"],
    "installable": True,
    "application": True,
}
