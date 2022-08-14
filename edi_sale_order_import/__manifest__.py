# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# TODO: deprecate
{
    "name": "EDI Sale order import",
    "summary": """Plug sale_order_import into EDI machinery.""",
    "version": "14.0.1.1.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "depends": ["edi_oca", "sale_order_import"],
    "auto_install": True,
    "data": ["templates/exchange_chatter_msg.xml"],
}
