# Copyright 2021 Camptocamp
# @author: Iván Todorovich <ivan.todorovich@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice Factur-X Buyer Reference",
    "version": "14.0.1.0.0",
    "category": "Invoicing Management",
    "license": "AGPL-3",
    "summary": "Set a Buyer Reference to be used in Factur-X/ZUGFeRD invoices",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        "account_invoice_facturx",
    ],
    "data": [
        "views/res_partner.xml",
    ],
}
