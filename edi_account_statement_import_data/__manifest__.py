# Copyright 2022 APPSTOGROW
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI account statement import data",
    "summary": """Plug account statement import into EDI machinery.""",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "Cybrosys,Odoo Community Association (OCA)",
    "maintainers": ["appstogrow"],
    "depends": ["edi_account_statement_import"],
    "data": [
        "data/edi_backend_type.xml",
        "data/edi_exchange_type.xml",
    ],
}
