# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import HttpCase
from odoo.tools import mute_logger

from .common import TestPunchoutIdsCommon


class TestPunchoutIdsController(HttpCase, TestPunchoutIdsCommon):
    """End-to-end HTTP tests for ``/punchout/ids/receive/<backend_id>``.

    Exercises the controller with a ``warenkorb`` form field as a
    real IDS supplier would post back, including the
    ``punchout_session_token`` query param introduced for unambiguous
    session matching.
    """

    def _post_ids(self, backend, warenkorb_xml, query=""):
        url = f"/punchout/ids/receive/{backend.id}"
        if query:
            url = f"{url}?{query}"
        return self.url_open(
            url, data={"warenkorb": warenkorb_xml}, allow_redirects=False
        )

    def test_controller_happy_path_with_token(self):
        """``warenkorb`` POST with the matching session token flips
        the session to ``to_process`` and redirects."""
        xml = self._get_sample_ids_xml()
        response = self._post_ids(
            self.backend,
            xml,
            query=f"punchout_session_token={self.session.buyer_cookie_id}",
        )
        self.assertEqual(response.status_code, 303)
        self.session.invalidate_recordset()
        self.assertEqual(self.session.state, "to_process")

    @mute_logger(
        "odoo.addons.punchout_ids.models.punchout_session",
        "odoo.addons.punchout_ids.controllers.main",
    )
    def test_controller_unknown_token_does_not_match(self):
        """A token that doesn't match any session is rejected; the
        controller still redirects so the user's browser doesn't see
        an error, but no session is touched."""
        xml = self._get_sample_ids_xml()
        response = self._post_ids(
            self.backend, xml, query="punchout_session_token=does-not-exist"
        )
        self.assertEqual(response.status_code, 303)
        self.session.invalidate_recordset()
        self.assertEqual(self.session.state, "draft")

    @mute_logger("odoo.addons.punchout_ids.controllers.main")
    def test_controller_oversized_payload_rejected(self):
        """A payload above the backend's ``max_response_size`` is
        rejected; the receive endpoint redirects without storing
        anything on the session."""
        self.backend.max_response_size = 100  # bytes
        xml = "<IDS>" + ("x" * 1000) + "</IDS>"
        response = self._post_ids(
            self.backend,
            xml,
            query=f"punchout_session_token={self.session.buyer_cookie_id}",
        )
        self.assertEqual(response.status_code, 303)
        self.session.invalidate_recordset()
        self.assertEqual(self.session.state, "draft")
        self.assertFalse(self.session.response)
