# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI Sale order import UBL",
    "summary": """Plug sale_order_import_ubl into EDI machinery.""",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "depends": ["edi_ubl_oca", "edi_sale_order_import", "sale_order_import_ubl"],
    "auto_install": True,
    "data": ["data/edi_exchange_type.xml"],
}
