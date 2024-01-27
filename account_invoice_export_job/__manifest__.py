# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Account Invoice Export Job",
    "version": "16.0.1.0.0",
    "category": "Invoicing Management",
    "license": "AGPL-3",
    "summary": "",
    "author": "Camptocamp SA, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["account_invoice_export", "queue_job"],
    "maintainers": ["TDu"],
    "data": [
        "data/queue_job_data.xml",
    ],
    "installable": True,
    "auto_install": True,
}
