# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI Sales",
    "summary": """
        Configuration and special behaviors for EDI on sales.
    """,
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        "sale_order_import_ubl",
        "edi_sale_oca",
        "edi_ubl_oca",
        "edi_xml_oca",
        "edi_exchange_template_oca",
        "edi_exchange_template_party_data",
        "edi_state_oca",
        # This could be made optional
        # but the delivery part would need another source of data
        "sale_stock",
    ],
    "data": [
        "data/edi_state.xml",
        "templates/qweb_tmpl_party.xml",
        "templates/qweb_tmpl_order_response.xml",
        "views/sale_order.xml",
    ],
    "demo": [
        "demo/edi_exchange_type.xml",
        "demo/exc_templ_order_response.xml",
    ],
}
