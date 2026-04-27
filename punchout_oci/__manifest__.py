# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Punchout OCI",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "summary": "OCI (Open Catalog Interface) protocol support for Punchout",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA)",
    "maintainers": ["hbrunn"],
    "website": "https://github.com/OCA/edi",
    "depends": [
        "punchout",
    ],
    "data": [
        "views/punchout_backend.xml",
    ],
    "demo": [
        "demo/punchout_oci_demo.xml",
    ],
}
