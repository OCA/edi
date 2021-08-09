# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Base UBL",
    "version": "13.0.2.3.0",
    "category": "Hidden",
    "license": "AGPL-3",
    "summary": "Base module for Universal Business Language (UBL)",
    "author": "Akretion,Onestein,Odoo Community Association (OCA)",
    "website": "https://github.com/oca/edi/",
    "depends": ["uom_unece", "account_tax_unece", "base_vat"],
    "external_dependencies": {"python": ["PyPDF2"]},
    "installable": True,
}
