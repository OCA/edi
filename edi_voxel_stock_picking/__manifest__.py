# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Voxel stock picking",
    "summary": "Sends stock picking report to Voxel.",
    "version": "11.0.1.0.0",
    "category": "Warehouse Management",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/oca/edi/",
    "license": "AGPL-3",
    "depends": [
        "stock",
        "edi_voxel",
    ],
    "data": [
        "views/report_voxel_picking.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
}
