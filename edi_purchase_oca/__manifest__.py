# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "EDI Purchase",
    "summary": """
        Define EDI Configuration for Purchase Orders""",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["purchase", "edi_oca", "component_event"],
    "data": ["views/purchase_order_views.xml", "views/edi_exchange_record_views.xml"],
    "demo": [],
}
