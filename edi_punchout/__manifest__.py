# Copyright 2023 Hunki Enterprises BV (https://hunki-enterprises.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Punchout",
    "summary": "Create purchase orders directly from supplier webshops",
    "version": "13.0.1.0.0",
    "development_status": "Alpha",
    "category": "Purchase Management",
    "website": "https://github.com/OCA/edi",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA)",
    "maintainers": ["hbrunn"],
    "license": "AGPL-3",
    "depends": ["purchase"],
    "data": [
        "data/uom_uom.xml",
        "security/edi_punchout.xml",
        "security/ir.model.access.csv",
        "views/edi_punchout_account.xml",
        "views/edi_punchout_transaction.xml",
        "views/purchase_order.xml",
        "views/templates.xml",
        "views/uom_uom.xml",
    ],
    "demo": ["demo/edi_punchout_account.xml"],
}
