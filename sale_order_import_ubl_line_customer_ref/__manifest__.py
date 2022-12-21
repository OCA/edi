# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Sale Order UBL Import - Import order line customer ref",
    "version": "14.0.1.0.0",
    "category": "Sales Management",
    "license": "AGPL-3",
    "summary": "Extract specific customer reference for each order line",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    # NOTE: the dependency on *ubl is probably not mandatory
    # but that's the only module ATM providing a value for `note`
    # and since at this time the module is tested only with UBL we leave it like this.
    "depends": ["sale_order_import_ubl", "sale_stock_line_customer_ref"],
    "installable": True,
    "auto_install": True,
}
