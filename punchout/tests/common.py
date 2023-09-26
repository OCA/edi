# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from uuid import uuid4

from odoo.tests.common import SavepointCase


class TestPunchoutCommon(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_model = cls.env["punchout.backend"]
        cls.request_model = cls.env["punchout.request"]
        cls.buyer_cookie_encryption_key = "9Ndn3znJUntZpwF51nXsMokf1Xt0X3jjolMX-AD5_W0="
        cls.backend = cls.backend_model.create(
            {
                "name": uuid4(),
                "from_domain": "from",
                "from_identity": "from",
                "to_domain": "to",
                "to_identity": "to",
                "url": "/",
                "shared_secret": "/",
                "user_agent": "/",
                "deployment_mode": "test",
                "browser_form_post_url": "/punchout/cxml/receive/",
                "buyer_cookie_encryption_key": cls.buyer_cookie_encryption_key,
            }
        )

        cls.request = cls.request_model.create(
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
        return self.request_model._store_punchout_request(self.backend.id, cxml_string,)
