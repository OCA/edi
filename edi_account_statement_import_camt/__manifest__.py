{
    "name": "EDI account statement import CAMT",
    "summary": """Plug account statement import into EDI machinery.""",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    # "author": "Cybrosys,Odoo Community Association (OCA)",
    "maintainers": ["Cybrosys"],
    "depends": ["edi_ubl_oca", "edi_account_statement_import", "account_statement_import_camt"],
    "auto_install": True,
    "data": ["data/edi_exchange_type.xml"],
}
