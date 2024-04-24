# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Base Import Pdf Simple Pdftotext",
    "version": "15.0.1.0.0",
    "website": "https://github.com/OCA/edi",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["base_import_pdf_simple"],
    "installable": True,
    "external_dependencies": {
        "python": ["pdftotext"],
    },
    "maintainers": ["victoralmau"],
}
