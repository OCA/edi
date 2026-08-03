# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Edi local",
    "summary": "Edi local",
    "version": "17.0.1.0.0",
    "author": "Binhex,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "license": "AGPL-3",
    "depends": ["base", "mail"],
    "data": [
        "security/edi_local_security.xml",
        "security/ir.model.access.csv",
        "data/edi_local_header_data.xml",
        "data/ir_cron_data.xml",
        "views/edi_local_line_views.xml",
        "views/edi_local_views.xml",
        "views/edi_local_header_views.xml",
        "views/edi_local_menus_views.xml",
    ],
    "installable": True,
}
