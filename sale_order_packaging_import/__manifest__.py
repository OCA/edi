# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Sale Order Packaging Import",
    "version": "14.0.1.1.0",
    "category": "Sales Management",
    "license": "AGPL-3",
    "summary": "Import the packaging on the sale order line",
    "author": "Camptocamp SA,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        "sale_stock",
        "sale_order_import",
        # OCA sale-workflow
        "sale_order_line_packaging_qty",
    ],
    "development_status": "Alpha",
    "installable": True,
}
