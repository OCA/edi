# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Electronic Document",
    "summary": """
        Base module for EDI Communication""",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["mail", "component"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/edi_document.xml",
        "views/edi_format.xml",
    ],
    "demo": [],
}
