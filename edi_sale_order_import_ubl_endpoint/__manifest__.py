# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI Sale order import UBL endpoint",
    "summary": """Provide a default endpoint to import SO in UBL format.""",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "depends": ["edi_sale_order_import", "sale_order_import_ubl", "edi_endpoint_oca"],
    "auto_install": True,
    "data": ["data/endpoint.xml"],
}
