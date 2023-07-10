# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Product Import",
    "version": "14.0.1.1.1",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "summary": "Import product catalogues",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        "stock",
        # OCA/edi
        "base_business_document_import",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings.xml",
        "wizard/product_import_view.xml",
    ],
}
