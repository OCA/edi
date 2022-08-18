# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI Sale order import",
    "summary": """
    MODULE DEPRECATED: use `edi_sale_oca`.

    Plug sale_order_import into EDI machinery.""",
    "version": "14.0.1.1.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    # Depend on edi_sale_oca which now provides the component.
    "depends": ["edi_sale_oca"],
    "auto_install": False,
    "data": ["templates/exchange_chatter_msg.xml"],
    "post_load": "post_load_hook",
}
