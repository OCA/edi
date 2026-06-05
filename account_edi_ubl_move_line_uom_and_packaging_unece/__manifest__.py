# Copyright 2026 ACSONE SA/NV, BCIM
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account EDI UBL move line uom and packaging By UNECE",
    "summary": """Adds UNECE-based detection of UoM and packaging on invoice
    lines during UBL import.""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, BCIM,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        "account_move_line_packaging",
        "account_edi_ubl_cii",
        "uom_unece",
        "product_packaging_unece",
    ],
    "data": ["views/account_move.xml"],
    "demo": [],
}
