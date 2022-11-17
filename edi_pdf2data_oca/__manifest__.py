# Copyright 2021 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Pdf2data Import",
    "summary": """
        Module that allows to import data from a pdf""",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "author": "CreuBlanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["edi_oca"],
    "external_dependencies": {
        "python": ["dateparser==1.1.1"],
        "deb": ["poppler-utils"],
    },
    "maintainers": ["etobella"],
    "data": [
        "wizards/pdf2data_template_import_yml.xml",
        "data/edi_data.xml",
        "security/ir.model.access.csv",
        "views/pdf2data_template.xml",
        "wizard/pdf2data_import.xml",
    ],
}
