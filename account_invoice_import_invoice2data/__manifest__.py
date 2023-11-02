# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice Import Invoice2data",
    "version": "14.0.2.1.2",
    "category": "Accounting/Accounting",
    "license": "AGPL-3",
    "summary": "Import supplier invoices using the invoice2data lib",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via", "bosd"],
    "website": "https://github.com/OCA/edi",
    "depends": ["account_invoice_import"],
    "external_dependencies": {
        "python": [
            "invoice2data",
            "dateparser",
        ],
        "deb": ["poppler-utils"],
    },
    "data": ["wizard/account_invoice_import_view.xml"],
    "demo": ["demo/demo_data.xml"],
    "installable": True,
}
