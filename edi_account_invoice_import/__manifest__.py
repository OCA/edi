# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# @author: Lois Rilo <lois.rilo@forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI Account Invoice Import",
    "summary": """Plug account_invoice_import into EDI machinery.""",
    "version": "14.0.1.1.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "ForgeFlow,Odoo Community Association (OCA)",
    "maintainers": ["LoisRForgeFlow"],
    "depends": ["edi_oca", "account_invoice_import"],
    "auto_install": True,
    "data": ["templates/exchange_chatter_msg.xml"],
}
