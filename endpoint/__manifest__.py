# Copyright 2021 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Endpoint",
    "summary": """Provide custom endpoint machinery.""",
    "version": "14.0.2.2.0",
    "license": "LGPL-3",
    "development_status": "Beta",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "website": "https://github.com/OCA/web-api",
    "depends": ["endpoint_route_handler", "rpc_helper"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/endpoint_view.xml",
    ],
    "demo": [
        "demo/endpoint_demo.xml",
    ],
    "post_init_hook": "post_init_hook",
}
