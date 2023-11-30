# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Despatch Advice Import",
    "summary": """
        Despatch Advice import""",
    "version": "16.0.1.0.0",
    "website": "https://github.com/OCA/edi",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "depends": ["purchase", "base_business_document_import_stock"],
    "data": ["wizard/despatch_advice_import.xml"],
    "demo": [],
    "installable": True,
}
