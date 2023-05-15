# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI Product import UBL",
    "summary": """Plug product_import_ubl into EDI machinery.""",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "depends": ["edi_ubl_oca", "edi_product_import", "product_import_ubl"],
    "data": ["data/edi_exchange_type.xml"],
}
