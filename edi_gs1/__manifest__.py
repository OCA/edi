# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Base GS1 EDI",
    "summary": """
        Base module for GS1 standard EDI exchange""",
    "version": "13.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "ACSONE,Odoo Community Association (OCA)",
    "depends": ["component", "edi_exchange_template", "edi_xml", "uom"],
    "external_dependencies": {"python": ["xmlschema", "xmlunittest"]},
    "data": [
        "security/gs1_backend_acl.xml",
        "data/gs1_backend_data.xml",
        "data/ack_in_exchange_type_data.xml",
        "data/ack_out_exchange_type_data.xml",
        "data/business_header_qweb_template.xml",
        "data/business_header_output_template.xml",
        "data/contact_details_qweb_template.xml",
        "views/res_partner.xml",
        "views/edi_backend.xml",
        "views/uom_uom.xml",
    ],
    "post_init_hook": "post_init_hook",
}
