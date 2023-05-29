# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI sale endpoint integration",
    "summary": """
        Glue module between edi_sale_oca and edi_endpoint_oca.
    """,
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "website": "https://github.com/OCA/edi",
    "depends": [
        "edi_sale_oca",
        "edi_endpoint_oca",
    ],
    "data": [
        "views/sale_order.xml",
    ],
    "auto_install": True,
}
