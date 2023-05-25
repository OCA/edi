# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "EDI Bank Statement",
    "summary": """
        Define EDI Configuration for Bank Statements""",
    "version": "13.0.1.0.0",
    "license": "LGPL-3",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["account", "edi", "component_event"],
    "data": [
        "views/account_bank_statement_views.xml",
        "views/edi_exchange_record_views.xml",
    ],
    "demo": [],
}
