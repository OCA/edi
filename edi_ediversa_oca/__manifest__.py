# Copyright 2025 Manuel Regidor <manuel.regidor@qubiq.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "EDI - Ediversa",
    "summary": "Ediversa - Base Module",
    "version": "17.0.1.0.0",
    "category": "EDI",
    "website": "https://github.com/OCA/edi",
    "author": "Sygel, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "edi_exchange_template_oca",
    ],
    "data": [
        "data/edi.xml",
        "data/ir_config_parameter.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
    ],
}
