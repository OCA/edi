# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Account Invoice Export",
    "version": "16.0.1.0.0",
    "category": "Invoicing Management",
    "license": "AGPL-3",
    "development_status": "Beta",
    "summary": "",
    "author": "Camptocamp SA, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["account", "account_invoice_transmit_method"],
    "maintainers": ["TDu"],
    "data": [
        "data/mail_activity_type.xml",
        "views/transmit_method.xml",
        "views/account_move.xml",
        "views/message_template.xml",
    ],
    "installable": True,
}
