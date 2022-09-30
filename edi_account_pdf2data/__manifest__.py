# Copyright 2022 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Edi Account Pdf2data",
    "summary": """
        Import Account moves with PDF2Data""",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "CreuBlanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["edi_account", "edi_pdf2data", "purchase"],
    "data": ["data/edi_data.xml", "wizards/account_move_import_pdf2data.xml"],
    "demo": [],
}
