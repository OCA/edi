# Copyright 2017-2023 Therp BV
# Copyright 2025-2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Account Invoice Import Invoice2data DB Templates",
    "version": "16.0.1.0.0",
    "category": "Accounting/Accounting",
    "license": "AGPL-3",
    "summary": (
        "Store invoice2data templates in the database; use them alongside the "
        "disk-based ones during invoice import."
    ),
    "author": "Therp BV,bosd,Odoo Community Association (OCA)",
    "maintainers": ["bosd"],
    "website": "https://github.com/OCA/edi",
    "depends": ["account_invoice_import_invoice2data"],
    "external_dependencies": {
        "python": [
            "invoice2data",
        ],
    },
    "data": [
        "security/invoice2data_template_groups.xml",
        "security/ir.model.access.csv",
        "views/invoice2data_template.xml",
    ],
    "installable": True,
}
