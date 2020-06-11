# Copyright 2016-2020 Akretion France
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice Factur-X",
    "version": "13.0.1.0.0",
    "category": "Invoicing Management",
    "license": "AGPL-3",
    "summary": "Generate Factur-X/ZUGFeRD customer invoices",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/edi",
    "depends": [
        "account_e-invoice_generate",
        "account_payment_partner",
        "base_facturx",
        "base_vat",
    ],
    "external_dependencies": {"python": ["facturx"]},
    "data": [
        "views/res_partner.xml",
        "views/res_config_settings.xml",
        "views/report_invoice.xml",
    ],
    "post_init_hook": "set_xml_format_in_pdf_invoice_to_facturx",
    "uninstall_hook": "remove_facturx_xml_format_in_pdf_invoice",
    "installable": True,
}
