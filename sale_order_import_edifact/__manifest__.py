# Copyright 2023 ALBA Software S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Import Business Document EDIFACT/D96A Order",
    "summary": "EDIFACT/D96A Order",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "category": "Sales Management",
    "website": "https://github.com/OCA/edi",
    "author": "ALBA Software, Odoo Community Association (OCA)",
    "maintainers": ["rmorant"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "sale_management",
        "partner_identification",
        "partner_identification_gln",
        "base_edifact",
        "edi_sale_order_import",
    ],
    "data": [
        "wizard/sale_order_import_view.xml",
    ],
    "demo": ["demo/demo_data.xml"],
}
