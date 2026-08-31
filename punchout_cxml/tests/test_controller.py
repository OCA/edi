# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os
from base64 import b64encode

from odoo.tests.common import HttpCase
from odoo.tools import mute_logger

from .common import TestPunchoutCxmlCommon

PATH = os.path.dirname(os.path.abspath(__file__))


class TestPunchoutCxmlController(HttpCase, TestPunchoutCxmlCommon):
    """End-to-end HTTP tests for ``/punchout/cxml/receive/<backend_id>``.

    Exercises the controller against a live Odoo HTTP layer with
    realistic supplier-callback payloads, so the route signature,
    auth=none decorator, payload-size guard, and session-state
    transition are covered together.
    """

    def _post_cxml(self, backend, payload, encode_b64=True):
        """POST a cXML payload to the receive endpoint as a supplier
        would (form-encoded, no auth, no CSRF token)."""
        if encode_b64:
            data = {"cXML-base64": b64encode(payload.encode()).decode()}
        else:
            data = {"cxml-urlencoded": payload}
        return self.url_open(
            f"/punchout/cxml/receive/{backend.id}",
            data=data,
            allow_redirects=False,
        )

    def test_controller_happy_path_sets_to_process(self):
        """Valid cXML payload with a known BuyerCookie flips the
        session to ``to_process`` and redirects."""
        cxml = self._get_response_xml_content(PATH, "test_store_request.xml")
        response = self._post_cxml(self.backend, cxml)
        self.assertEqual(response.status_code, 303)  # redirect
        self.session.invalidate_recordset()
        self.assertEqual(self.session.state, "to_process")

    @mute_logger(
        "odoo.addons.punchout_cxml.models.punchout_session",
        "odoo.addons.punchout_cxml.controllers.main",
    )
    def test_controller_unknown_buyer_cookie(self):
        """Payload with a buyer cookie that doesn't match any session
        still redirects (so the user's browser doesn't error) but no
        session is updated."""
        cxml = self._get_response_xml_content(PATH, "test_unknown_buyer_cookie_id.xml")
        response = self._post_cxml(self.backend, cxml)
        self.assertEqual(response.status_code, 303)
        self.session.invalidate_recordset()
        self.assertEqual(self.session.state, "draft")

    @mute_logger("odoo.addons.punchout_cxml.controllers.main")
    def test_controller_oversized_payload_rejected(self):
        """A payload above the backend's ``max_response_size`` is
        rejected; the receive endpoint redirects without storing
        anything on the session."""
        self.backend.max_response_size = 100  # bytes
        cxml = "x" * 1000  # well over the cap
        response = self._post_cxml(self.backend, cxml, encode_b64=False)
        self.assertEqual(response.status_code, 303)
        self.session.invalidate_recordset()
        self.assertEqual(self.session.state, "draft")
        self.assertFalse(self.session.response)
