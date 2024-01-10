# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI Sales",
    "summary": """
        Configuration and special behaviors for EDI on sales.
    """,
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "website": "https://github.com/OCA/edi-framework",
    "depends": [
        "edi_oca",
        "edi_record_metadata_oca",
        "sale_order_import",
    ],
    "data": [
        "data/job_function.xml",
        "views/sale_order.xml",
        "views/edi_exchange_record.xml",
        "templates/exchange_chatter_msg.xml",
    ],
}
