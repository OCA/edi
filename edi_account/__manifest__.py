# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Electronic Document for Account",
    "summary": """
        Account module for EDI Communication""",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["edi", "account"],
    "data": [
        "views/account_journal.xml",
        "views/res_partner.xml",
        "data/edi_format.xml",
        "views/account_move.xml",
        "wizards/account_invoice_send.xml",
    ],
    "demo": ["demo/edi_format.xml"],
}
