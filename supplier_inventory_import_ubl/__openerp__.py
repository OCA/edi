# -*- coding: utf-8 -*-
# © 2020 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Supplier Inventory Import UBL",
    "summary": "Import vendor inventory on vendor info",
    "version": "8.0.1.0.0",
    "website": "https://github.com/oca/edi",
    "author": " Akretion, Odoo Community Association (OCA)",
    "category": "Purchases",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["base_ubl", "base_business_document_import_stock"],
    "data": [
        "views/product_view.xml",
        "views/supplierinfo_view.xml",
        "views/stock_view.xml",
        "views/company_view.xml",
        "wizards/inventory_import_view.xml",
    ],
    "demo": ["demo/partner.xml", "demo/product.xml"],
    "maintainers": ["bealdav"],
}
