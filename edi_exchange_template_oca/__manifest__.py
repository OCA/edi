# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI Exchange Template",
    "summary": """Allows definition of exchanges via templates.""",
    "version": "13.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "ACSONE,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "depends": ["edi", "component"],
    "data": [
        "security/ir_model_access.xml",
        "views/edi_exchange_template_output_views.xml",
    ],
}
