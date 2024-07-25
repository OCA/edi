# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Account Invoice Export",
    "version": "13.0.1.2.3",
    "category": "Invoicing Management",
    "license": "AGPL-3",
    "summary": "",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["account_invoice_transmit_method", "queue_job"],
    "data": [
        "data/mail_activity_type.xml",
        "views/transmit_method.xml",
        "views/account_move.xml",
        "views/message_template.xml",
    ],
    "installable": True,
}
