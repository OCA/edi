# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Base WAMAS - UBL",
    "summary": """Base module to aggregate WAMAS - UBL features.""",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "website": "https://github.com/OCA/edi",
    "license": "AGPL-3",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "depends": ["base_ubl", "base_wamas"],
    "data": [
        "security/ir_model_access.xml",
        "data/ir_config_parameter_data.xml",
        "data/ir_actions_server_data.xml",
        "data/wamas_document_field_data.xml",
        "data/wamas_document_default_field_template_data.xml",
        "data/wamas_document_element_data.xml",
        "data/wamas_document_xml_conversion_template_data.xml",
        "data/wamas_document_xml_conversion_field_data.xml",
        "views/wamas_document_field_views.xml",
        "views/wamas_document_default_field_template_views.xml",
        "views/wamas_document_element_views.xml",
        "views/wamas_document_xml_conversion_field_views.xml",
        "views/wamas_document_xml_conversion_template_views.xml",
        "views/wamas_menus.xml",
    ],
}
