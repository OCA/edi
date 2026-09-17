# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import HttpCase


class TestPunchoutOciMockSupplier(HttpCase):
    def test_catalog_renders(self):
        resp = self.url_open(
            "/punchout_oci_mock_supplier/catalog"
            "?HOOK_URL=http://127.0.0.1:8069/punchout/oci/receive/1"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"<form", resp.content)
        self.assertIn(b'name="qty_MOCK-EA-001"', resp.content)
        # All five mock rows should be present.
        for sku in (
            "MOCK-EA-001",
            "MOCK-PCE-002",
            "MOCK-M-003",
            "MOCK-L-004",
            "MOCK-KG-005",
        ):
            self.assertIn(sku.encode(), resp.content)

    def test_checkout_returns_interstitial(self):
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        hook_url = f"{base}/punchout/oci/receive/1"
        resp = self.url_open(
            "/punchout_oci_mock_supplier/checkout",
            data={
                "hook_url": hook_url,
                "qty_MOCK-EA-001": "2",
                "qty_MOCK-KG-005": "1.5",
            },
        )
        self.assertEqual(resp.status_code, 200)
        # Two items selected × 9 OCI keys = 18 hidden fields.
        self.assertEqual(resp.content.count(b'name="NEW_ITEM-'), 18)
        self.assertIn(hook_url.encode(), resp.content)

    def test_checkout_blocks_external_hook_url(self):
        resp = self.url_open(
            "/punchout_oci_mock_supplier/checkout",
            data={"hook_url": "https://evil.example.com/x", "qty_MOCK-EA-001": "1"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_checkout_rejects_empty_cart(self):
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        resp = self.url_open(
            "/punchout_oci_mock_supplier/checkout",
            data={"hook_url": f"{base}/punchout/oci/receive/1"},
        )
        self.assertEqual(resp.status_code, 400)
