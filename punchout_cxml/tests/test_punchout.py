# Copyright 2023 ACSONE SA/NV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os

from odoo.tools import mute_logger

from .common import TestPunchoutCxmlCommon

PATH = os.path.dirname(os.path.abspath(__file__))


class TestPunchoutCxml(TestPunchoutCxmlCommon):
    def test_store_request(self):
        cxml_string = self._get_response_xml_content(PATH, "test_store_request.xml")
        session = self._store_response(cxml_string)
        session.invalidate_recordset()
        self.assertEqual(session.state, "to_process")
        self.assertTrue(bool(session.response))

    @mute_logger("odoo.addons.punchout_cxml.models.punchout_session")
    def test_unknown_buyer_cookie_id(self):
        cxml_string = self._get_response_xml_content(
            PATH, "test_unknown_buyer_cookie_id.xml"
        )
        result = self._store_response(cxml_string)
        self.assertFalse(result)

    def test_action_test_connection_rejects_non_cxml(self):
        """The Test Connection action only makes sense for cXML
        backends — calling it on an OCI/IDS one raises clearly."""
        from odoo.exceptions import UserError

        # Flip the backend to a non-cxml protocol via SQL so we don't
        # need protocol modules installed for this assertion.
        self.env.cr.execute(
            "UPDATE punchout_backend SET protocol = 'unknown' WHERE id = %s",
            (self.backend.id,),
        )
        self.backend.invalidate_recordset()
        with self.assertRaises(UserError):
            self.backend.action_test_connection()
