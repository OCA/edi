# Copyright 2023 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)
{
    "name": "Account Invoice EDIFACT",
    "summary": "Generate customer invoices with EDIFACT/D96A format",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Invoicing Management",
    "website": "https://github.com/OCA/edi",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "sale_management",
        "account",
        "base_edifact",
    ],
    "data": [],
    "demo": [
        "demo/data_demo.xml",
    ],
}
