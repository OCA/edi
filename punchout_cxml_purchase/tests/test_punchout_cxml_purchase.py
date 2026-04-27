# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools import mute_logger

from odoo.addons.punchout_purchase.tests.common import TestPunchoutPurchaseCommon

CXML_CART = """<?xml version="1.0"?>
<cXML>
  <Message>
    <PunchOutOrderMessage>
      <PunchOutOrderMessageHeader operationAllowed="edit">
        <Total><Money currency="USD">100.00</Money></Total>
      </PunchOutOrderMessageHeader>
      <ItemIn quantity="2">
        <ItemID>
          <SupplierPartID>SKU-CXML-1</SupplierPartID>
        </ItemID>
        <ItemDetail>
          <UnitPrice><Money currency="USD">50.00</Money></UnitPrice>
          <Description xml:lang="en">Test cXML Widget</Description>
          <UnitOfMeasure>EA</UnitOfMeasure>
        </ItemDetail>
      </ItemIn>
    </PunchOutOrderMessage>
  </Message>
</cXML>"""


class TestPunchoutCxmlPurchase(TestPunchoutPurchaseCommon):
    def test_parse_cxml_cart(self):
        self.session.response = CXML_CART
        lines = self.session._prepare_purchase_order_lines()
        self.assertEqual(len(lines), 1)
        _, _, vals = lines[0]
        self.assertEqual(vals["product_qty"], 2.0)
        self.assertEqual(vals["price_unit"], 50.0)
        self.assertEqual(vals["name"], "Test cXML Widget")

    def test_empty_response_returns_no_lines(self):
        self.session.response = False
        self.assertEqual(self.session._prepare_purchase_order_lines(), [])

    @mute_logger("odoo.addons.punchout_cxml_purchase.models.punchout_session")
    def test_malformed_xml_returns_no_lines(self):
        self.session.response = "not xml"
        self.assertEqual(self.session._prepare_purchase_order_lines(), [])

    @mute_logger("odoo.addons.punchout_oci_purchase.models.punchout_session")
    def test_wrong_protocol_defers_to_super(self):
        # Switching to OCI lets the OCI override try to json.loads our cXML
        # XML; mute its expected parse-error log so OCA CI doesn't trip.
        self.backend.protocol = "oci"
        self.session.response = CXML_CART
        # Base _prepare_purchase_order_lines returns [] — cxml override must not fire.
        self.assertEqual(self.session._prepare_purchase_order_lines(), [])

    def test_auto_creates_product(self):
        self.session.response = CXML_CART
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        product = self.env["product.product"].browse(vals["product_id"])
        self.assertTrue(product.exists())
        self.assertEqual(product.seller_ids.product_code, "SKU-CXML-1")

    def test_post_create_product_hook_called_once_on_create(self):
        """_post_create_product_hook fires on auto-create; raw_data
        carries supplier_part_id + description + unit_price + the raw
        item_detail element so overrides can pull cXML-specific fields
        without re-parsing."""
        from unittest.mock import patch

        self.session.response = CXML_CART
        with patch.object(
            type(self.session),
            "_post_create_product_hook",
            autospec=True,
        ) as hook:
            self.session._prepare_purchase_order_lines()
        self.assertEqual(hook.call_count, 1)
        _self, product, raw_data = hook.call_args[0]
        self.assertTrue(product.exists())
        self.assertEqual(raw_data.get("supplier_part_id"), "SKU-CXML-1")
        self.assertIn("item_detail", raw_data)

    def test_post_create_product_hook_skipped_on_existing_match(self):
        from unittest.mock import patch

        self.env["product.product"].create(
            {
                "name": "Pre-existing cXML",
                "type": "consu",
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": self.partner.id,
                            "product_code": "SKU-CXML-1",
                        },
                    )
                ],
            }
        )
        self.session.response = CXML_CART
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
                "name": "Existing Widget",
                "type": "consu",
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": self.partner.id,
                            "product_code": "SKU-CXML-1",
                        },
                    )
                ],
            }
        )
        self.session.response = CXML_CART
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        self.assertEqual(vals["product_id"], existing.id)

    def test_no_auto_create_falls_back_to_existing_purchase_product(self):
        """auto_create_products=False: missing product → fallback to any
        purchasable product in the database, no auto-creation."""
        self.backend.auto_create_products = False
        # Pre-create a purchasable product so the fallback search has a hit.
        self.env["product.product"].create(
            {"name": "Fallback purchasable", "type": "consu", "purchase_ok": True}
        )
        product_count_before = self.env["product.product"].search_count([])
        self.session.response = CXML_CART
        lines = self.session._prepare_purchase_order_lines()
        self.assertEqual(len(lines), 1)
        product_count_after = self.env["product.product"].search_count([])
        self.assertEqual(product_count_after, product_count_before)

    def test_no_unit_of_measure_falls_back_to_unit(self):
        """When the cXML item carries no <UnitOfMeasure>, default to Units."""
        cart_no_uom = CXML_CART.replace("<UnitOfMeasure>EA</UnitOfMeasure>", "")
        self.session.response = cart_no_uom
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        self.assertEqual(vals["product_uom"], self.env.ref("uom.product_uom_unit").id)

    def test_invalid_unit_price_handled(self):
        """A non-numeric UnitPrice is treated as 0.0 instead of raising."""
        cart_bad_price = CXML_CART.replace(
            '<Money currency="USD">50.00</Money>',
            '<Money currency="USD">not-a-number</Money>',
            1,
        )
        # Outer Total is fine; we need to corrupt the inner UnitPrice/Money only.
        # CXML_CART has Money 100.00 (Total) and Money 50.00 (UnitPrice). Replace
        # the second occurrence — both happen to be 50.00 only once, so target
        # the UnitPrice block instead.
        cart_bad_price = CXML_CART.replace(
            '<UnitPrice><Money currency="USD">50.00</Money></UnitPrice>',
            '<UnitPrice><Money currency="USD">not-a-number</Money></UnitPrice>',
        )
        self.session.response = cart_bad_price
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        self.assertEqual(vals["price_unit"], 0.0)

    def test_uom_mapping_is_used(self):
        """Backend UoM mapping for 'EA' overrides the UNECE/name fallback."""
        dozen = self.env.ref("uom.product_uom_dozen")
        self.env["punchout.uom.mapping"].create(
            {
                "backend_id": self.backend.id,
                "supplier_code": "EA",
                "uom_id": dozen.id,
            }
        )
        self.session.response = CXML_CART
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        self.assertEqual(vals["product_uom"], dozen.id)
