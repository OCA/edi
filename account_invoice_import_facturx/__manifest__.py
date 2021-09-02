# Copyright 2015-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice Import Factur-X",
    "version": "14.0.1.0.0",
    "category": "Invoicing Management",
    "license": "AGPL-3",
    "summary": "Import Factur-X/ZUGFeRD supplier invoices/refunds",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/edi",
    "depends": ["account_invoice_import", "base_facturx"],
    "external_dependencies": {"python": ["factur-x"]},
    "data": ["wizard/account_invoice_import_view.xml"],
    "demo": ["demo/demo_data.xml"],
    "installable": True,
}
