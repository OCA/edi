# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os

from odoo.tools import mute_logger

from .common import TestPunchoutCommon

PATH = os.path.dirname(os.path.abspath(__file__))


class TestPunchout(TestPunchoutCommon):
    def test_store_request(self):
        cxml_string = self._get_response_xml_content(PATH, "test_store_request.xml")
        session = self._store_response(cxml_string)
        session.invalidate_cache([])
        self.assertEqual(session.state, "to_process")
        self.assertTrue(bool(session.cxml_response))

    @mute_logger("odoo.addons.punchout.models.punchout_request")
    def test_unknown_buyer_cookie_id(self):
        cxml_string = self._get_response_xml_content(
            PATH, "test_unknown_buyer_cookie_id.xml"
        )
        result = self._store_response(cxml_string)
        self.assertFalse(result)
