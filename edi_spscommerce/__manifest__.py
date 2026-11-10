# Copyright 2026 Gray Matter Logic
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "EDI SPS Commerce",
    "summary": "SPS Commerce RSX XML: inbound Orders, outbound Shipments and Invoices on OCA EDI framework",
    "version": "19.0.1.0.0",
    "license": "LGPL-3",
    "development_status": "Alpha",
    "website": "https://github.com/OCA/edi-framework",
    "author": "Gray Matter Logic",
    "category": "Operations/EDI",
    "depends": [
        "edi_core_oca",
        "edi_storage_oca",
        "edi_exchange_template_oca",
        "sale_stock",
        "account",
    ],
    "external_dependencies": {
        "python": ["xmltodict"],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/edi_backend_type.xml",
        "data/edi_backend.xml",
        "data/edi_exchange_templates.xml",
        "data/edi_exchange_type_orders.xml",
        "data/edi_exchange_type_shipments.xml",
        "data/edi_exchange_type_invoices.xml",
        "views/edi_sps_import_views.xml",
    ],
    "installable": True,
    "application": False,
}
