# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Punchout IDS Purchase",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Create purchase orders from IDS shopping carts",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA)",
    "maintainers": ["hbrunn"],
    "website": "https://github.com/OCA/edi",
    "depends": [
        "punchout_ids",
        "punchout_purchase",
    ],
    "external_dependencies": {"python": ["lxml"]},
    "auto_install": True,
}
