# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Punchout OCI Mock Supplier",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Self-contained mock OCI supplier for end-to-end testing",
    "author": "Bosd, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi",
    "depends": [
        # Depend on the OCI purchase glue (rather than just punchout_oci)
        # so installing this demo module pulls in everything needed for
        # the cart-to-PO roundtrip — partner_id on the backend, the
        # Create PO action, the OCI cart parser. Without it, clicking
        # "Access" on the demo backend would land in a session that
        # can't auto-create a PO.
        "punchout_oci_purchase",
    ],
    "data": [
        "templates/mock_catalog_templates.xml",
    ],
    "demo": [
        "demo/punchout_oci_mock_supplier_demo.xml",
    ],
    "development_status": "Beta",
}
