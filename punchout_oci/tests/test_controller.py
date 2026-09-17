# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import HttpCase
from odoo.tools import mute_logger

from .common import TestPunchoutOciCommon


class TestPunchoutOciController(HttpCase, TestPunchoutOciCommon):
    """End-to-end HTTP tests for ``/punchout/oci/receive/<backend_id>``.

    Exercises the controller with form-encoded NEW_ITEM payloads as
    a real OCI supplier would post back, including the
    ``punchout_session_token`` query param introduced for unambiguous
    session matching.
    """

    def _post_oci(self, backend, form_data, query=""):
        url = f"/punchout/oci/receive/{backend.id}"
        if query:
            url = f"{url}?{query}"
        return self.url_open(url, data=form_data, allow_redirects=False)

    def test_controller_happy_path_with_token(self):
        """Form-data POST with the matching session token flips the
        session to ``to_process`` and redirects."""
        form = self._get_sample_oci_form_data()
        response = self._post_oci(
            self.backend,
            form,
            query=f"punchout_session_token={self.session.buyer_cookie_id}",
        )
        self.assertEqual(response.status_code, 303)
        self.session.invalidate_recordset()
        self.assertEqual(self.session.state, "to_process")

    @mute_logger(
        "odoo.addons.punchout_oci.models.punchout_session",
        "odoo.addons.punchout_oci.controllers.main",
    )
    def test_controller_unknown_token_does_not_match(self):
        """A token that doesn't match any session is rejected; the
        controller still redirects so the user's browser doesn't see
        an error, but no session is touched."""
        form = self._get_sample_oci_form_data()
        response = self._post_oci(
            self.backend, form, query="punchout_session_token=does-not-exist"
        )
        self.assertEqual(response.status_code, 303)
        self.session.invalidate_recordset()
        self.assertEqual(self.session.state, "draft")

    @mute_logger("odoo.addons.punchout_oci.controllers.main")
    def test_controller_oversized_payload_rejected(self):
        """A payload above the backend's ``max_response_size`` is
        rejected; the receive endpoint redirects without storing
        anything on the session."""
        self.backend.max_response_size = 100  # bytes
        # Single field with a huge value pushes total form-data JSON
        # well past 100 bytes after json.dumps.
        form = {"NEW_ITEM-DESCRIPTION[1]": "x" * 1000}
        response = self._post_oci(
            self.backend,
            form,
            query=f"punchout_session_token={self.session.buyer_cookie_id}",
        )
        self.assertEqual(response.status_code, 303)
        self.session.invalidate_recordset()
        self.assertEqual(self.session.state, "draft")
        self.assertFalse(self.session.response)
