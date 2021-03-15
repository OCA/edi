# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "EDI Exchange Template",
    "summary": """Allows definition of exchanges via templates.""",
    "version": "13.0.1.5.1",
    "development_status": "Alpha",
    "license": "LGPL-3",
    "author": "ACSONE,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "depends": ["edi", "component"],
    "data": [
        "security/ir_model_access.xml",
        "views/edi_exchange_template_output_views.xml",
    ],
}
