# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "EDI Account Payment Order",
    "summary": """
        Define EDI Configuration for Account Payment Order""",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["account_payment_order", "edi_account", "component_event"],
    "data": [
        "views/account_payment_order_views.xml",
        "views/edi_exchange_record_views.xml",
    ],
    "demo": [],
}
