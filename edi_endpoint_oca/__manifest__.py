# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "EDI endpoint",
    "summary": """
    Base module allowing configuration of custom endpoints for EDI framework.
    """,
    "version": "14.0.1.2.0",
    "development_status": "Alpha",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "depends": ["base_edi", "edi_oca", "endpoint"],
    "data": [
        "security/ir.model.access.csv",
        "views/edi_backend_views.xml",
        "views/edi_endpoint_views.xml",
    ],
    "demo": ["demo/edi_backend_demo.xml"],
}
