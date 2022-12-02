# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "EDI Party data",
    "summary": """
    Allow to configure and retrieve party information for EDI exchanges.
    """,
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/edi",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "depends": ["edi_oca", "partner_identification"],
    "data": [
        "views/edi_exchange_type_views.xml",
    ],
}
