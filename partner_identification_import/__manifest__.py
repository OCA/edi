# Copyright 2020 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Partner Identification Import",
    "version": "14.0.1.0.0",
    "category": "Tools",
    "license": "AGPL-3",
    "summary": "Provides partner matching on extra ID",
    "author": "BCIM, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        "base_business_document_import",
        # OCA/partner-contact
        "partner_identification",
    ],
}
