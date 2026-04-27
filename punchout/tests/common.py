# Copyright 2023 ACSONE SA/NV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from uuid import uuid4

from odoo.tests.common import TransactionCase


class TestPunchoutCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_model = cls.env["punchout.backend"]
        cls.session_model = cls.env["punchout.session"]
        cls.backend = cls.backend_model.create(
            {
                "name": str(uuid4()),
                "description": str(uuid4()),
                "protocol": "cxml",
                "url": "https://example.com/punchout",
                "browser_form_post_url": "/punchout/receive/",
            }
        )

        cls.session = cls.session_model.create(
            {
                "backend_id": cls.backend.id,
                "buyer_cookie_id": "2-cc162436-fcab-4cfb-888d-abfd8708520d",
            }
        )
