# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "EDI Sending Warning",
    "version": "14.0.1.0.0",
    "summary": "Module for handling errors in EDI sending",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "category": "Uncategorized",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "depends": [
        "edi_oca",
        "edi_purchase_oca",
        # purchase-workflow
        "purchase_order_sending_warning",
    ],
    "data": [],
    "installable": True,
}
