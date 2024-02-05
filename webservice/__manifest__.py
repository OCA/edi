# Copyright 2020 Creu Blanca
# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    "name": "WebService",
    "summary": """
        Defines webservice abstract definition to be used generally""",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "development_status": "Production/Stable",
    "maintainers": ["etobella"],
    "author": "Creu Blanca, Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/web-api",
    "depends": ["component", "server_environment"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/webservice_backend.xml",
    ],
    "demo": [],
}
