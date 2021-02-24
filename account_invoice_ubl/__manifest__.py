# Copyright 2016-2018 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice UBL",
    "version": "14.0.1.0.0",
    "category": "Accounting & Finance",
    "license": "AGPL-3",
    "summary": "Generate UBL XML file for customer invoices/refunds",
    "author": "Akretion,Onestein,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        "account_einvoice_generate",
        "account_payment_partner",
        "base_ubl_payment",
        "account_tax_unece",
    ],
    "data": ["views/account_move.xml", "views/res_config_settings.xml"],
    "post_init_hook": "set_xml_format_in_pdf_invoice_to_ubl",
    "uninstall_hook": "remove_ubl_xml_format_in_pdf_invoice",
    "installable": True,
}
