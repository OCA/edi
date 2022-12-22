# Copyright 2022 Odoo Community Association
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Edi Stock Oca",
    "summary": """
       Define EDI Configuration for Stock""",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "author": "Odoo Community Association,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["stock", "edi_oca", "component_event"],
    "data": ["views/stock_picking.xml", "views/res_partner.xml"],
    "demo": [],
}
