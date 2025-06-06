# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Ediversa - Invoice Export",
    "summary": "Send customer invoices to Ediversa",
    "version": "17.0.1.0.0",
    "category": "EDI",
    "website": "https://github.com/OCA/edi",
    "author": "Sygel, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale_stock",
        "edi_ediversa_oca",
        "edi_account_oca",
    ],
    "data": [
        "data/edi.xml",
        "views/res_partner_views.xml",
        "views/account_tax_views.xml",
    ],
}
