# Copyright 2020 ACSONE
# Copyright 2021 Camptocamp
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "EDI",
    "summary": """
    Define backends, exchange types, exchange records,
    basic automation and views for handling EDI exchanges.
    """,
    "version": "14.0.1.21.0",
    "website": "https://github.com/OCA/edi",
    "development_status": "Beta",
    "license": "LGPL-3",
    "author": "ACSONE,Creu Blanca,Camptocamp,Odoo Community Association (OCA)",
    "maintainers": ["simahawk", "etobella"],
    "depends": [
        "base_edi",
        "component_event",
        "mail",
        "base_sparse_field",
        "queue_job",
    ],
    "external_dependencies": {"python": ["pyyaml"]},
    "data": [
        "wizards/edi_exchange_record_create_wiz.xml",
        "data/cron.xml",
        "data/sequence.xml",
        "data/job_channel.xml",
        "data/job_function.xml",
        "security/res_groups.xml",
        "security/ir_model_access.xml",
        "views/edi_backend_views.xml",
        "views/edi_backend_type_views.xml",
        "views/edi_exchange_record_views.xml",
        "views/edi_exchange_type_views.xml",
        "views/edi_exchange_type_rule_views.xml",
        "views/menuitems.xml",
        "templates/exchange_chatter_msg.xml",
        "templates/exchange_mixin_buttons.xml",
        "templates/assets.xml",
    ],
    "qweb": ["static/src/xml/widget_edi.xml"],
    "demo": ["demo/edi_backend_demo.xml"],
}
