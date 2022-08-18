# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI Sale order import UBL (DEPRECATED)",
    "summary": """
    MODULE DEPRECATED: use `edi_sale_ubl_oca`.

    Plug sale_order_import_ubl into EDI machinery.
    """,
    "version": "14.0.1.1.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "depends": ["edi_sale_ubl_oca"],
    "auto_install": False,
    "demo": ["demo/edi_exchange_type.xml"],
    "post_load": "post_load_hook",
}
