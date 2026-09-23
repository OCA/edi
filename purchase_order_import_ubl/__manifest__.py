# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Quotation Order UBL Import",
    "version": "18.0.1.0.0",
    "category": "Purchase Management",
    "license": "AGPL-3",
    "summary": "Import UBL XML quotation files",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        # OCA/edi
        "base_ubl_parse",
        "purchase_order_import",
        # OCA/reporting-engine
        "pdf_xml_attachment",
    ],
    "installable": True,
}
