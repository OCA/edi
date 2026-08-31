# Copyright 2023 ACSONE SA/NV
# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from uuid import uuid4

from odoo.tests.common import TransactionCase


class TestPunchoutPurchaseCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_model = cls.env["punchout.backend"]
        cls.session_model = cls.env["punchout.session"]

        # Create a partner (supplier)
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Supplier",
                "supplier_rank": 1,
            }
        )

        # Create backend with partner
        cls.backend = cls.backend_model.create(
            {
                "name": str(uuid4()),
                "description": str(uuid4()),
                "protocol": "cxml",
                "url": "https://example.com/punchout",
                "browser_form_post_url": "/punchout/receive/",
                "partner_id": cls.partner.id,
                "auto_create_products": True,
            }
        )

        cls.session = cls.session_model.create(
            {
                "backend_id": cls.backend.id,
                "buyer_cookie_id": str(uuid4()),
                "state": "to_process",
            }
        )
