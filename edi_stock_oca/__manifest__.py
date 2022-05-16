# Copyright 2022 Odoo Community Association
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Edi Stock Oca",
    "summary": """
       Define EDI Configuration for Stock""",
    "version": "13.0.1.0.1",
    "license": "AGPL-3",
    "author": "Odoo Community Association,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["stock", "edi", "component_event"],
    "data": ["views/stock_picking.xml", "views/res_partner.xml"],
    "demo": [],
}
