# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Pdf2data Import",
    "summary": """
        Module that allows to import data from a pdf""",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Creu Blanca,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["edi", "account"],
    "external_dependencies": {
        "python": ["dateparser", "unidecode"],
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
