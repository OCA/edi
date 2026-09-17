# Copyright 2023 ACSONE SA/NV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Punchout cXML",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "summary": "cXML protocol support for Punchout",
    "author": "Odoo Community Association (OCA), ACSONE SA/NV",
    "website": "https://github.com/OCA/edi",
    "depends": [
        "punchout",
    ],
    "data": [
        "data/cxml_common.xml",
        "data/cxml_punchout_setup_request.xml",
        "views/punchout_backend.xml",
    ],
    "demo": [
        "demo/punchout_cxml_demo.xml",
    ],
    "external_dependencies": {"python": ["lxml"]},
}
