# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from uuid import uuid4

from odoo.tests.common import TransactionCase


class TestPunchoutOciCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_model = cls.env["punchout.backend"]
        cls.session_model = cls.env["punchout.session"]
        cls.backend = cls.backend_model.create(
            {
                "name": str(uuid4()),
                "description": str(uuid4()),
                "protocol": "oci",
                "url": "https://supplier.example.com/catalog",
                "browser_form_post_url": "/punchout/oci/receive/",
                # OCI-specific fields
                "oci_version": "5.0",
                "oci_custom_parameters": "username=test&password=secret",
            }
        )

        cls.session = cls.session_model.create(
            {
                "backend_id": cls.backend.id,
                "buyer_cookie_id": str(uuid4()),
            }
        )

    def _get_sample_oci_form_data(self):
        """Return sample OCI form data as would be received from supplier."""
        return {
            "NEW_ITEM-DESCRIPTION[1]": "Test Product 1",
            "NEW_ITEM-QUANTITY[1]": "10",
            "NEW_ITEM-PRICE[1]": "99.99",
            "NEW_ITEM-UNIT[1]": "EA",
            "NEW_ITEM-VENDORMAT[1]": "SKU001",
            "NEW_ITEM-DESCRIPTION[2]": "Test Product 2",
            "NEW_ITEM-QUANTITY[2]": "5",
            "NEW_ITEM-PRICE[2]": "49.50",
            "NEW_ITEM-UNIT[2]": "EA",
            "NEW_ITEM-VENDORMAT[2]": "SKU002",
            "NEW_ITEM-LEADTIME[2]": "7",
        }
