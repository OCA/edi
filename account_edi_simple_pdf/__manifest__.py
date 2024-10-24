# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Import Simple PDF",
    "version": "15.0.4.0.0",
    "category": "Accounting/Accounting",
    "license": "AGPL-3",
    "summary": "Import simple PDF vendor bills",
    "author": "Akretion,Hunki Enterprises BV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["account_edi"],
    "external_dependencies": {
        "python": [
            "regex",
            "dateparser",
            "pypdf>=3.1.0",
        ],
        "deb": ["libmupdf-dev", "mupdf", "mupdf-tools", "poppler-utils"],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner.xml",
        "views/account_invoice_import_simple_pdf_fields.xml",
        "views/account_invoice_import_simple_pdf_invoice_number.xml",
    ],
    "demo": ["demo/demo_data.xml"],
    "installable": True,
    "application": True,
}
