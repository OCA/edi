# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice Import Simple PDF",
    "version": "14.0.2.2.1",
    "category": "Accounting/Accounting",
    "license": "AGPL-3",
    "summary": "Import simple PDF vendor bills",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/edi",
    "depends": ["account_invoice_import"],
    # "excludes": ["account_invoice_import_invoice2data"],
    "external_dependencies": {
        "python": ["pdfplumber", "regex", "dateparser==1.1.1"],
        "deb": ["libmupdf-dev", "mupdf", "mupdf-tools", "poppler-utils"],
    },
    "data": [
        "security/ir.model.access.csv",
        "wizard/account_invoice_import_view.xml",
        "views/res_partner.xml",
        "views/account_invoice_import_simple_pdf_fields.xml",
        "views/account_invoice_import_simple_pdf_invoice_number.xml",
    ],
    "demo": ["demo/demo_data.xml"],
    "installable": True,
    "application": True,
}
