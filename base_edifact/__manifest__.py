# Copyright 2023 ALBA Software S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Base EDIFACT",
    "summary": "UN/EDIFACT/D96A utilities using pydifact parser",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "category": "Tools",
    "website": "https://github.com/OCA/edi",
    "author": "ALBA Software, PlanetaTIC, Odoo Community Association (OCA)",
    "maintainers": ["rmorant"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    # "preloadable": True,
    "external_dependencies": {
        "python": ["pydifact"],
        "bin": [],
    },
    "depends": [
        "edi_party_data_oca",
        # for configuration
        "account",
        "partner_identification",
        "partner_identification_gln",
    ],
    "data": [],
}
