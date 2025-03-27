# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Voxel stock picking",
    "summary": "Sends stock picking report to Voxel.",
    "version": "15.0.1.1.2",
    "category": "Warehouse Management",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "license": "AGPL-3",
    "depends": ["edi_voxel_oca", "product_expiry", "sale_stock"],
    "data": [
        "data/ir_cron_data.xml",
        "views/report_voxel_picking.xml",
        "views/stock_picking_views.xml",
        "views/res_company_view.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_view.xml",
    ],
    "installable": True,
}
