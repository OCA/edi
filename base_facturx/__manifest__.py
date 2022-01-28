# Copyright 2016-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Base Factur-X",
    "version": "15.0.1.0.0",
    "category": "Invoicing Management",
    "license": "AGPL-3",
    "summary": "Base module for Factur-X/ZUGFeRD",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/edi",
    "depends": ["uom_unece", "account_tax_unece", "account_payment_unece"],
    "data": ["data/zugferd_codes.xml"],
    "installable": True,
}
