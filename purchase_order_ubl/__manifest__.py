# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Purchase Order UBL",
    "version": "18.0.1.0.0",
    "category": "Purchase Management",
    "license": "AGPL-3",
    "summary": "Embed UBL XML file inside the PDF purchase order",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        # Odoo/core
        "purchase",
        # OCA/edi
        "base_ubl_generate",
        # OCA/community-data-files
        "account_tax_unece",
        # OCA/reporting-engine
        "pdf_xml_attachment",
    ],
    "installable": True,
}
