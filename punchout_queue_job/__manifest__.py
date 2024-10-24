# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Punchout Queue Job",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA), ACSONE SA/NV",
    "website": "https://github.com/OCA/edi",
    "depends": [
        # oca/connector
        "queue_job",
        # oca/edi
        "punchout",
    ],
    "data": ["views/punchout_session.xml"],
    "demo": [],
}
