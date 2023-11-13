# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Punchout",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA), ACSONE SA/NV",
    "website": "https://github.com/OCA/edi",
    "depends": [
        # odoo addons
        "base",
        "mail",
    ],
    "data": [
        "security/punchout_backend.xml",
        "security/punchout_session.xml",
        "data/cxml/common.xml",
        "data/cxml/punchout_setup_request.xml",
        "views/punchout_backend.xml",
        "views/punchout_session.xml",
    ],
    "external_dependencies": {"python": ["lxml"]},
}
