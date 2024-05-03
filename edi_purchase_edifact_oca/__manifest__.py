# Copyright 2024 Trobz
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)
{
    "name": "EDI PURCHASE EDIFACT OCA",
    "summary": "Create and send EDIFACT order files",
    "version": "12.0.1.0.0",
    "development_status": "Alpha",
    "website": "https://github.com/OCA/edi",
    "author": "Trobz, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base_edifact",
        "stock",
        "edi_storage_oca",
        "edi_purchase_oca",
        "partner_identification_gln",
        "base_business_document_import",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/purchase.xml",
        "views/res_partner.xml",
        "data/edi_backend.xml",
        "data/edi_exchange_type.xml",
        "wizard/purchase_order_import_view.xml",
    ],
}
