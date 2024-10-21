# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Test Base Import Pdf by Template",
    "version": "17.0.1.1.0",
    "website": "https://github.com/OCA/edi",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["purchase", "base_import_pdf_by_template"],
    "installable": True,
    "demo": [
        "demo/base_import_pdf_template.xml",
    ],
    "maintainers": ["victoralmau"],
    "post_init_hook": "post_init_hook",
}
