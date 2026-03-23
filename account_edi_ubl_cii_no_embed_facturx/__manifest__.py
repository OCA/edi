# Copyright 2026 BCIM srl
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Edi Ubl Cii No Embed Factur-X",
    "summary": """Prevent to add a factur-x xml attachment inside every invoice""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "BCIM, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        "account_edi_ubl_cii",
    ],
    "data": [
        "data/account_edi_format.xml",
    ],
    "demo": [],
}
