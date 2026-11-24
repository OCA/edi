# Copyright 2026 ACSONE SA/NV,BCIM
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Edi Ubl Cii Retrieve Tax By Account Prefix",
    "summary": """Glue module between `account_invoice_tax_allowed_account_prefix`
    and `account_edi_ubl_cii_retrieve_tax` to filter taxes by account prefix
    during UBL import""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,BCIM,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        "account_edi_ubl_cii_retrieve_tax",
        "account_invoice_tax_allowed_account_prefix",
    ],
    "data": [],
    "demo": [],
    "maintainers": ["sbejaoui", "jbaudoux"],
}
