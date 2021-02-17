# Copyright 2017-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Py3o Factur-x Invoice",
    "version": "14.0.1.0.0",
    "category": "Invoicing Management",
    "license": "AGPL-3",
    "summary": "Generate Factur-X invoices with Py3o reporting engine",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/edi",
    "depends": ["account_invoice_facturx", "report_py3o"],
    "external_dependencies": {"python": ["factur-x"]},
    "installable": True,
}
