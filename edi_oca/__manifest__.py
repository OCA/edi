# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Base EDI Backend",
    "summary": """Base module to define EDI backends""",
    "version": "13.0.1.11.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "ACSONE,Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "depends": ["base_edi", "component", "component_event", "mail"],
    "data": [
        "data/cron.xml",
        "data/sequence.xml",
        "security/ir_model_access.xml",
        "views/edi_backend_views.xml",
        "views/edi_backend_type_views.xml",
        "views/edi_exchange_record_views.xml",
        "views/edi_exchange_type_views.xml",
        "views/menuitems.xml",
        "templates/exchange_chatter_msg.xml",
    ],
    "demo": ["demo/edi_backend_demo.xml"],
}
