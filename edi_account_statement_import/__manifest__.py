# Copyright 2022 APPSTOGROW
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI account statement import",
    "summary": """Plug account statement import into EDI machinery.""",
    "version": "14.0.1.1.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "Cybrosys,Odoo Community Association (OCA)",
    "maintainers": ["appstogrow"],
    "depends": ["edi_oca", "account_statement_import"],
    "auto_install": True,
    "data": ["templates/exchange_chatter_msg.xml"],
}
