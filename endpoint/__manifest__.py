# Copyright 2021 Camptcamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Endpoint",
    "summary": """Provide custom endpoint machinery.""",
    "version": "14.0.1.0.1",
    "license": "LGPL-3",
    "development_status": "Alpha",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "website": "https://github.com/OCA/edi",
    "depends": ["endpoint_route_handler"],
    "data": [
        "security/ir.model.access.csv",
        "views/endpoint_view.xml",
    ],
    "demo": [
        "demo/endpoint_demo.xml",
    ],
}
