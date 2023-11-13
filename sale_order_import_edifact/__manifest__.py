# Copyright 2023 ALBA Software S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Import Business Document EDIFACT/D96A Order",
    "summary": "EDIFACT/D96A Order",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Sales Management",
    "website": "https://github.com/OCA/edi",
    "author": "ALBA Software, Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["rmorant"],
    "license": "AGPL-3",
    "depends": [
        "sale_management",
        "partner_identification_gln",
        "base_edifact",
        "sale_order_import",
    ],
    "data": [
        "wizard/sale_order_import_view.xml",
    ],
    "demo": ["demo/demo_data.xml"],
}
