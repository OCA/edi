# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools import mute_logger

from .common import TestPunchoutIdsCommon


class TestPunchoutIds(TestPunchoutIdsCommon):
    def test_ids_protocol_available(self):
        """Test that IDS protocol is available in selection."""
        protocols = dict(self.backend_model._selection_protocol())
        self.assertIn("ids", protocols)
        self.assertEqual(protocols["ids"], "IDS")

    def test_ids_backend_creation(self):
        """Test that IDS backend is created with correct values."""
        self.assertTrue(self.backend.id)
        self.assertEqual(self.backend.protocol, "ids")
        self.assertEqual(self.backend.ids_version, "2.5")
        self.assertEqual(self.backend.ids_name_kunde, "TestCustomer")

    def test_ids_setup_url_generation(self):
        """Test that IDS catalog URL is generated correctly."""
        url = self.session_model._get_post_punchout_setup_url(self.session)
        self.assertIn("hook_url=", url)
        self.assertIn("name_kunde=TestCustomer", url)
        self.assertIn("kndnr=CUST001", url)

    def test_ids_store_response(self):
        """Test storing IDS XML response."""
        xml_data = self._get_sample_ids_xml()

        session = self.session_model._store_punchout_session_response(
            self.backend.id, xml_data
        )

        self.assertTrue(session)
        self.assertEqual(session.state, "to_process")
        self.assertTrue(session.response)

    @mute_logger("odoo.addons.punchout_ids.models.punchout_session")
    def test_ids_invalid_xml(self):
        """Test that invalid XML is handled gracefully."""
        session = self.session_model._store_punchout_session_response(
            self.backend.id, "<invalid>xml"
        )
        self.assertTrue(session)
        self.assertEqual(session.state, "error")

    def test_ids_validate_response(self):
        """Test IDS response validation."""
        self.session.response = self._get_sample_ids_xml()
        result = self.session._validate_response()
        self.assertTrue(result.get("valid"))

    def test_ids_validate_response_no_order(self):
        """Test IDS response validation with no Order element."""
        self.session.response = "<IDS><Other>data</Other></IDS>"
        result = self.session._validate_response()
        self.assertFalse(result.get("valid"))
        self.assertIn("No Order element", result.get("error", ""))
