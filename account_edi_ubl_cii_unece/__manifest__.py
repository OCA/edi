# Copyright 2026 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "UBL/CII UNECE extension",
    "version": "20.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Extend native support for UNECE codes for UBL/CII",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/edi",
    "depends": ["account_edi_ubl_cii", "account_payment_method_base"],
    "data": [
        "views/account_tax.xml",
        "views/account_payment_method.xml",
    ],
    "installable": True,
}
