# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Edi WebService",
    "summary": """
        Defines webservice integration from EDI Exchange records""",
    "version": "13.0.1.2.1",
    "license": "AGPL-3",
    "development_status": "Beta",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["edi", "webservice"],
    "data": ["views/edi_backend.xml", "security/ir.model.access.csv"],
}
