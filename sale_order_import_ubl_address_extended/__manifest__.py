# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Sale Order UBL Import with Extended Addresses",
    "version": "18.0.1.0.0",
    "category": "Sales Management",
    "license": "AGPL-3",
    "summary": "Glue module to use sale orders' UBL import with extended addresses",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["sale_order_import_ubl", "base_address_extended"],
    "installable": True,
    # Auto-install to fix the inconsistent base behavior when both modules are installed
    "auto_install": True,
}
