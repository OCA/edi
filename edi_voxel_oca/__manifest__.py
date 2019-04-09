# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Voxel",
    "summary": "Base module for connecting with Voxel",
    "version": "11.0.1.0.0",
    "category": "Hidden",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/oca/edi/",
    "license": "AGPL-3",
    "depends": [
        "product",
        "report_xml",
        "base_iso3166",
        "queue_job",
    ],
    "data": [
        "data/data_voxel_connection.xml",
        "data/data_voxel_uom.xml",
        "views/res_company_view.xml",
        "views/account_tax_views.xml",
        "views/product_uom_views.xml",
        "views/res_config_settings_views.xml",
        "views/template_voxel_report.xml",
        "security/voxel_security.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
