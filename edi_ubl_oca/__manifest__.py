# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI UBL",
    "summary": """Define EDI backend type for UBL.""",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "depends": ["edi_oca", "base_ubl"],
    "auto_install": True,
    "data": [
        "data/edi_backend_type.xml",
    ],
    "demo": [
        "demo/edi_backend_demo.xml",
    ],
}
