# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "EDI Sale order import UBL endpoint",
    "summary": """
        Provide a default endpoint to import SO in UBL format.
    """,
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "depends": ["edi_sale_ubl_oca", "edi_endpoint_oca"],
    "data": ["data/endpoint.xml"],
}
