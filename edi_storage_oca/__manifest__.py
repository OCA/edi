# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "EDI Storage backend support",
    "summary": """
    Base module to allow exchanging files via storage backend (eg: SFTP).
    """,
    "version": "13.0.1.5.0",
    "development_status": "Alpha",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "ACSONE,Odoo Community Association (OCA)",
    "depends": ["edi", "storage_backend", "component"],
    "data": ["security/ir_model_access.xml", "views/edi_backend_views.xml"],
    "demo": ["demo/edi_backend_demo.xml"],
}
