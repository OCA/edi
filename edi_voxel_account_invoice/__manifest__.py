# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Voxel account invoice",
    "summary": "Sends account invoices to Voxel.",
    "version": "13.0.1.1.1",
    "category": "Accounting & Finance",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/oca/edi/",
    "license": "AGPL-3",
    "depends": ["edi_voxel", "stock_picking_invoice_link"],
    "data": [
        "data/ir_cron_data.xml",
        "views/account_move_views.xml",
        "views/report_voxel_invoice.xml",
        "views/res_company_view.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
