# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Voxel",
    "summary": "Base module for connecting with Voxel",
    "version": "13.0.1.0.0",
    "category": "Hidden",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/oca/edi/",
    "license": "AGPL-3",
    "depends": [
        "account",
        "product",
        "report_xml",
        "base_iso3166",
        "queue_job",
        "product_supplierinfo_for_customer",
    ],
    "data": [
        "security/voxel_security.xml",
        "security/ir.model.access.csv",
        "data/data_voxel_uom.xml",
        "views/res_company_view.xml",
        "views/account_tax_views.xml",
        "views/product_uom_views.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
        "views/template_voxel_report.xml",
        "views/voxel_login_views.xml",
    ],
    "installable": True,
}
