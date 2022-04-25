# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Base EDI",
    "summary": """Base module to aggregate EDI features.""",
    "version": "13.0.1.0.3",
    "development_status": "Beta",
    "license": "LGPL-3",
    "author": "ACSONE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "maintainers": ["simahawk"],
    "depends": ["base"],
    "data": [
        "data/module_category.xml",
        "security/edi_groups.xml",
        "views/edi_menu.xml",
    ],
}
