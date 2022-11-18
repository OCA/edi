# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# @author: Lois Rilo <lois.rilo@forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI Invoice import UBL",
    "summary": "Plug account_invoice_import_ubl into EDI machinery",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "maintainers": ["LoisRForgeFlow"],
    "depends": [
        "edi_ubl_oca",
        "edi_account_invoice_import",
        "account_invoice_import_ubl",
    ],
    "auto_install": True,
    "data": ["data/edi_exchange_type.xml"],
}
