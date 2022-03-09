# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Edi WebService",
    "summary": """
        Defines webservice integration from EDI Exchange records""",
    "version": "15.0.1.1.0",
    "license": "AGPL-3",
    "development_status": "Beta",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["edi_oca", "webservice"],
    "data": ["views/edi_backend.xml", "security/ir.model.access.csv"],
}
