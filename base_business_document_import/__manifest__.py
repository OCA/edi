# Copyright 2016-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Base Business Document Import",
    "version": "14.0.2.0.0",
    "category": "Tools",
    "license": "AGPL-3",
    "summary": "Provides technical tools to import sale orders or supplier invoices",
    "author": "Akretion, Nicolas JEUDY, Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/edi",
    "depends": [
        # OCA/community-data-files
        "account_tax_unece",
        "uom_unece",
    ],
    "external_dependencies": {"python": ["PyPDF2"]},
}
