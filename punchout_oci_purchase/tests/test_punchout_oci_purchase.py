# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo.tools import mute_logger

from odoo.addons.punchout_purchase.tests.common import TestPunchoutPurchaseCommon


def _oci_cart(**overrides):
    base = {
        "NEW_ITEM-DESCRIPTION[1]": "Test OCI Widget",
        "NEW_ITEM-QUANTITY[1]": "3",
        "NEW_ITEM-PRICE[1]": "25.00",
        "NEW_ITEM-VENDORMAT[1]": "OCI-SKU-1",
        "NEW_ITEM-UNIT[1]": "EA",
        "NEW_ITEM-LEADTIME[1]": "0",
    }
    base.update(overrides)
    return json.dumps(base)


class TestPunchoutOciPurchase(TestPunchoutPurchaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.protocol = "oci"

    def test_parse_oci_cart(self):
        self.session.response = _oci_cart()
        lines = self.session._prepare_purchase_order_lines()
        self.assertEqual(len(lines), 1)
        _, _, vals = lines[0]
        self.assertEqual(vals["product_qty"], 3.0)
        self.assertEqual(vals["price_unit"], 25.0)
        self.assertEqual(vals["name"], "Test OCI Widget")

    def test_multiple_items(self):
        self.session.response = json.dumps(
            {
                "NEW_ITEM-DESCRIPTION[1]": "First",
                "NEW_ITEM-QUANTITY[1]": "1",
                "NEW_ITEM-PRICE[1]": "10",
                "NEW_ITEM-VENDORMAT[1]": "A",
                "NEW_ITEM-UNIT[1]": "EA",
                "NEW_ITEM-DESCRIPTION[2]": "Second",
                "NEW_ITEM-QUANTITY[2]": "2",
                "NEW_ITEM-PRICE[2]": "20",
                "NEW_ITEM-VENDORMAT[2]": "B",
                "NEW_ITEM-UNIT[2]": "EA",
            }
        )
        lines = self.session._prepare_purchase_order_lines()
        self.assertEqual(len(lines), 2)

    def test_empty_response_returns_no_lines(self):
        self.session.response = False
        self.assertEqual(self.session._prepare_purchase_order_lines(), [])

    @mute_logger("odoo.addons.punchout_oci_purchase.models.punchout_session")
    def test_malformed_json_returns_no_lines(self):
        self.session.response = "not json"
        self.assertEqual(self.session._prepare_purchase_order_lines(), [])

    @mute_logger("odoo.addons.punchout_cxml_purchase.models.punchout_session")
    def test_wrong_protocol_defers_to_super(self):
        # Switching to cXML lets the cXML override try to XML-parse our OCI
        # JSON; mute its expected parse-error log so OCA CI doesn't trip.
        self.backend.protocol = "cxml"
        self.session.response = _oci_cart()
        self.assertEqual(self.session._prepare_purchase_order_lines(), [])

    def test_auto_creates_product(self):
        self.session.response = _oci_cart()
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        product = self.env["product.product"].browse(vals["product_id"])
        self.assertTrue(product.exists())
        self.assertEqual(product.seller_ids.product_code, "OCI-SKU-1")

    def test_post_create_product_hook_called_once_on_create(self):
        """_post_create_product_hook fires on auto-create only, not on
        existing-product matches. Verifies the hook signature carries
        (product, raw_data) and the raw_data dict contains the OCI
        cart-line keys (e.g., VENDORMAT) so overrides can pull
        protocol-specific fields without re-parsing the whole cart."""
        from unittest.mock import patch

        self.session.response = _oci_cart()
        with patch.object(
            type(self.session),
            "_post_create_product_hook",
            autospec=True,
        ) as hook:
            self.session._prepare_purchase_order_lines()
        self.assertEqual(hook.call_count, 1)
        # autospec → call_args[0] = (self.session, product, raw_data)
        _self, product, raw_data = hook.call_args[0]
        self.assertTrue(product.exists())
        self.assertEqual(raw_data.get("VENDORMAT"), "OCI-SKU-1")

    def test_post_create_product_hook_skipped_on_existing_match(self):
        """Hook fires on auto-create only — re-using an existing
        product (matched via supplierinfo) must NOT fire the hook
        (otherwise an enrichment override would re-fetch on every
        cart import for known products, burning API quota)."""
        from unittest.mock import patch

        self.env["product.product"].create(
            {
                "name": "Pre-existing OCI",
                "type": "consu",
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": self.partner.id,
                            "product_code": "OCI-SKU-1",
                        },
                    )
                ],
            }
        )
        self.session.response = _oci_cart()
        with patch.object(
            type(self.session),
            "_post_create_product_hook",
            autospec=True,
        ) as hook:
            self.session._prepare_purchase_order_lines()
        hook.assert_not_called()

    def test_reuses_existing_supplierinfo(self):
        existing = self.env["product.product"].create(
            {
                "name": "Existing OCI",
                "type": "consu",
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": self.partner.id,
                            "product_code": "OCI-SKU-1",
                        },
                    )
                ],
            }
        )
        self.session.response = _oci_cart()
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        self.assertEqual(vals["product_id"], existing.id)

    def test_no_auto_create_falls_back_to_existing_purchase_product(self):
        """auto_create_products=False: cart item has no matching product →
        fall back to any purchasable product, no creation."""
        self.backend.auto_create_products = False
        self.env["product.product"].create(
            {"name": "Fallback purchasable OCI", "type": "consu", "purchase_ok": True}
        )
        product_count_before = self.env["product.product"].search_count([])
        self.session.response = _oci_cart()
        lines = self.session._prepare_purchase_order_lines()
        self.assertEqual(len(lines), 1)
        product_count_after = self.env["product.product"].search_count([])
        self.assertEqual(product_count_after, product_count_before)

    def test_no_unit_falls_back_to_unit(self):
        """When OCI form has no UNIT entry, default to Units."""
        cart = json.loads(_oci_cart())
        del cart["NEW_ITEM-UNIT[1]"]
        self.session.response = json.dumps(cart)
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        self.assertEqual(vals["product_uom"], self.env.ref("uom.product_uom_unit").id)

    def test_longtext_propagates_to_product_description(self):
        """When LONGTEXT differs from DESCRIPTION it lands on
        product.description_purchase."""
        self.session.response = _oci_cart(
            **{
                "NEW_ITEM-LONGTEXT[1]": "Detailed multi-line description goes here",
            }
        )
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        product = self.env["product.product"].browse(vals["product_id"])
        self.assertEqual(
            product.description_purchase,
            "Detailed multi-line description goes here",
        )

    def test_uom_mapping_is_used(self):
        dozen = self.env.ref("uom.product_uom_dozen")
        self.env["punchout.uom.mapping"].create(
            {
                "backend_id": self.backend.id,
                "supplier_code": "EA",
                "uom_id": dozen.id,
            }
        )
        self.session.response = _oci_cart()
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        self.assertEqual(vals["product_uom"], dozen.id)
