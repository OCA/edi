# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "EDI Chunk Processing OCA",
    "summary": "Add a new component for spliting and processing file using chunk",
    "version": "14.0.1.0.0",
    "category": "Uncategorized",
    "website": "https://github.com/OCA/edi",
    "author": " Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "chunk_processing",
        "edi_oca",
    ],
    "data": [
        "views/edi_exchange_record_views.xml",
    ],
    "demo": [],
}
