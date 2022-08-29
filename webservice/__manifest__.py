# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "WebService",
    "summary": """
    Provide unified way to handle external webservices configuration and calls.
    """,
    "version": "14.0.1.3.0",
    "license": "AGPL-3",
    "development_status": "Beta",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/web-api",
    "depends": ["component", "server_environment"],
    "data": ["security/ir.model.access.csv", "views/webservice_backend.xml"],
    "maintainers": ["etobella", "simahawk"],
}
