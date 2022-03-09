# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "WebService",
    "summary": """
        Defines webservice abstract definition to be used generally""",
    "version": "14.0.1.1.0",
    "license": "AGPL-3",
    "development_status": "Beta",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["component", "server_environment"],
    "data": ["security/ir.model.access.csv", "views/webservice_backend.xml"],
    "demo": [],
}
