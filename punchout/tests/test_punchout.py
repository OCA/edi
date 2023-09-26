# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os

from odoo.tools import mute_logger

from .common import TestPunchoutCommon

PATH = os.path.dirname(os.path.abspath(__file__))


class TestPunchout(TestPunchoutCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_model = cls.env["punchout.backend"]
        cls.request_model = cls.env["punchout.request"]

        cls.backend = cls.backend_model.create(
            {
                "name": "/",
                "from_domain": "from",
                "from_identity": "from",
                "to_domain": "to",
                "to_identity": "to",
                "url": "/",
                "shared_secret": "/",
                "user_agent": "/",
                "deployment_mode": "test",
                "browser_form_post_url": "/punchout/cxml/receive/",
                "buyer_cookie_encryption_key": (
                    "9Ndn3znJUntZpwF51nXsMokf1Xt0X3jjolMX-AD5_W0="
                ),
            }
        )

        cls.request = cls.request_model.create(
            {
                "backend_id": cls.backend.id,
                "buyer_cookie_id": "2-cc162436-fcab-4cfb-888d-abfd8708520d",
            }
        )

    def test_store_request(self):
        cxml_string = self._get_response_xml_content(PATH, "test_store_request.xml")
        request = self._store_response(cxml_string)
        request.invalidate_cache([])
        self.assertEqual(request.state, "to_process")
        self.assertTrue(bool(request.cxml_response))

    @mute_logger("odoo.addons.punchout.models.punchout_request")
    def test_unknown_buyer_cookie_id(self):
        cxml_string = self._get_response_xml_content(
            PATH, "test_unknown_buyer_cookie_id.xml"
        )
        result = self._store_response(cxml_string)
        self.assertFalse(result)
