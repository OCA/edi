# Copyright 2016-2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice Factur-X",
    "version": "17.0.1.0.0",
    "category": "Invoicing Management",
    "license": "AGPL-3",
    "summary": "Generate Factur-X/ZUGFeRD customer invoices",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/edi",
    "depends": [
        "account_einvoice_generate",
        "account_payment_partner",
        "base_facturx",
        "base_vat",
    ],
    "external_dependencies": {"python": ["factur-x"]},
    "data": [
        "views/res_partner.xml",
        "views/account_move.xml",
        "views/res_config_settings.xml",
    ],
    "post_init_hook": "set_xml_format_in_pdf_invoice_to_facturx",
    "installable": True,
}
