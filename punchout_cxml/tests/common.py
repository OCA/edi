# Copyright 2023 ACSONE SA/NV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from uuid import uuid4

from odoo.tests.common import TransactionCase


class TestPunchoutCxmlCommon(TransactionCase):
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
                "url": "/",
                "browser_form_post_url": "/punchout/cxml/receive/",
                # cXML-specific fields
                "from_domain": "from",
                "from_identity": "from",
                "to_domain": "to",
                "to_identity": "to",
                "shared_secret": "secret",
                "user_agent": "Odoo Punchout",
                "deployment_mode": "test",
            }
        )

        cls.session = cls.session_model.create(
            {
                "backend_id": cls.backend.id,
                "buyer_cookie_id": "2-cc162436-fcab-4cfb-888d-abfd8708520d",
            }
        )

    def _get_response_xml_content(self, filepath, filename):
        filepath = f"{filepath}/cxml/{filename}"
        with open(filepath, "rb") as file:
            content = file.read()
        return content.decode()

    def _store_response(self, cxml_string):
        return self.session_model._store_punchout_session_response(
            self.backend.id,
            cxml_string,
        )
