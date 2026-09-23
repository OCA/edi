# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Sale Order Import with Partner ID Numbers",
    "version": "18.0.1.0.0",
    "category": "Sales Management",
    "license": "AGPL-3",
    "summary": "Glue module to use sale orders' import with partners' ID numbers",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["sale_order_import", "partner_identification"],
    "installable": True,
    # Auto-install allow import of ID numbers when importing invoice/delivery partners
    "auto_install": True,
}
