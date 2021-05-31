# Copyright 2016-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice Import UBL",
    "version": "14.0.1.0.0",
    "category": "Accounting & Finance",
    "license": "AGPL-3",
    "summary": "Import UBL XML supplier invoices/refunds",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": ["account_invoice_import", "base_ubl"],
    "data": ["wizard/account_invoice_import_view.xml"],
    "demo": ["demo/demo_data.xml"],
    "installable": True,
}
