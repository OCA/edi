# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Voxel account invoice oca",
    "summary": "Sends account invoices to Voxel.",
    "version": "17.0.1.0.1",
    "development_status": "Production/Stable",
    "category": "Accounting & Finance",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "license": "AGPL-3",
    "depends": ["edi_voxel_oca", "stock_picking_invoice_link"],
    "data": [
        "data/ir_cron_data.xml",
        "data/queue_job_function_data.xml",
        "views/account_move_views.xml",
        "views/report_voxel_invoice.xml",
        "views/res_company_view.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
