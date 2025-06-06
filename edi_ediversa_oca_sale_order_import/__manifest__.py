# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Ediversa - Sale Order Import",
    "summary": "Process sale orders from Ediversa",
    "version": "17.0.1.0.0",
    "category": "EDI",
    "website": "https://github.com/OCA/edi",
    "author": "Sygel, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["sale", "edi_ediversa_oca"],
    "data": [
        "data/edi.xml",
        "data/ir_cron.xml",
    ],
}
