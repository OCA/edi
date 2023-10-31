# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Order Import",
    "version": "16.0.1.2.0",
    "category": "Sales Management",
    "license": "AGPL-3",
    "summary": "Import RFQ or sale orders from files",
    "author": "Akretion, Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        # OCA/sale-workflow
        "sale_commercial_partner",
        # OCA/edi
        "base_business_document_import",
        # OCA/server-tools
        "onchange_helper",
        # TODO: this dependency should be removed
        # and support for PDF import should be moved to a glue module
        "pdf_helper",
    ],
    "data": ["security/ir.model.access.csv", "wizard/sale_order_import_view.xml"],
    "installable": True,
}
