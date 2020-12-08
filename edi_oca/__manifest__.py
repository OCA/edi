# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI",
    "summary": """
    Define backends, exchange types, exchange records,
    basic automation and views for handling EDI exchanges.
    """,
    "version": "13.0.1.13.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "ACSONE,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "depends": ["base_edi", "component_event", "mail", "base_sparse_field"],
    "external_dependencies": {"python": ["pyyaml"]},
    "data": [
        "wizards/edi_exchange_record_create.xml",
        "data/cron.xml",
        "data/sequence.xml",
        "security/res_groups.xml",
        "security/ir_model_access.xml",
        "views/edi_backend_views.xml",
        "views/edi_backend_type_views.xml",
        "views/edi_exchange_record_views.xml",
        "views/edi_exchange_type_views.xml",
        "views/menuitems.xml",
        "templates/exchange_chatter_msg.xml",
        "templates/exchange_mixin_buttons.xml",
        "templates/assets.xml",
    ],
    "qweb": ["static/src/xml/widget_edi.xml"],
    "demo": ["demo/edi_backend_demo.xml"],
}
