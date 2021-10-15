# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Sale Order Customer Free Reference",
    "version": "14.0.1.0.0",
    "category": "Sale",
    "license": "AGPL-3",
    "summary": "Splits the Customer Reference on sale orders into two fields. "
    "An Id and a Free reference. The existing field is transformed "
    "into a computed one.",
    "author": "Camptocamp SA, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["sale"],
    "data": ["views/sale_order.xml", "views/account_move.xml"],
    "installable": True,
}
