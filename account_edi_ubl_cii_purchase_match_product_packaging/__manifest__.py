# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Edi Ubl Cii Purchase Match Product Packaging",
    "summary": """Allows retrieving the correct UoM and packaging from UNECE codes
    when matching invoice lines with purchase orders""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "maintainers": ["sbejaoui"],
    "depends": [
        "account_edi_ubl_cii_purchase_match",
        "account_edi_ubl_move_line_uom_and_packaging_unece",
    ],
    "data": [],
    "demo": [],
}
