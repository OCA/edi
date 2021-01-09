# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Sale Order Import Http",
    "version": "14.0.1.0.0",
    "category": "Sales Management",
    "license": "AGPL-3",
    "summary": "Add an HTTP endpoint to import UBL formatted orders"
    "automatically as sales order",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["auth_api_key", "queue_job", "sale_order_import_ubl"],
    "data": [
        "data/queue_job_data.xml",
        "data/res_users.xml",
    ],
    "installable": True,
}
