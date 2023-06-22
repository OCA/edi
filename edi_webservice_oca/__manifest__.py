# Copyright 2020 Creu Blanca
# Copyright 2022 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI WebService",
    "summary": """
        Defines webservice integration from EDI Exchange records""",
    "version": "14.0.1.4.0",
    "license": "AGPL-3",
    "development_status": "Beta",
    "author": "Creu Blanca, Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["etobella", "simahawk"],
    "website": "https://github.com/OCA/edi",
    "depends": ["edi_oca", "webservice"],
    "data": [
        "security/ir.model.access.csv",
        "views/edi_backend.xml",
        "views/edi_exchange_record.xml",
    ],
    "demo": ["demo/edi_backend.xml"],
}
