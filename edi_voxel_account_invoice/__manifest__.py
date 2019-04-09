# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Voxel account invoice",
    "summary": "Sends account invoices to Voxel.",
    "version": "11.0.1.0.0",
    "category": "Accounting & Finance",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/oca/edi/",
    "license": "AGPL-3",
    "depends": [
        "account_invoicing",
        "edi_voxel",
        "stock_picking_invoice_link",
    ],
    "data": [
        "views/account_invoice_views.xml",
        "views/report_voxel_invoice.xml",
    ],
    "installable": True,
}
