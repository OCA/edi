# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools import mute_logger

from odoo.addons.punchout_purchase.tests.common import TestPunchoutPurchaseCommon

IDS_CART = """<?xml version="1.0" encoding="UTF-8"?>
<IDS>
  <Order>
    <OrderInfo>
      <Cur>EUR</Cur>
      <DeliveryDate>2099-01-15</DeliveryDate>
    </OrderInfo>
    <OrderItem>
      <ArtNo>ART-1</ArtNo>
      <Kurztext>Schraubendreher Set</Kurztext>
      <Qty>2</Qty>
      <QU>ST</QU>
      <NetPrice>29.98</NetPrice>
      <VAT>19</VAT>
    </OrderItem>
  </Order>
</IDS>"""


class TestPunchoutIdsPurchase(TestPunchoutPurchaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.write(
            {
                "protocol": "ids",
                "ids_version": "2.5",
                "ids_name_kunde": "TestCustomer",
                "ids_kndnr": "CUST001",
                "ids_pw_kunde": "secret",
            }
        )

    def test_parse_ids_cart(self):
        self.session.response = IDS_CART
        lines = self.session._prepare_purchase_order_lines()
        self.assertEqual(len(lines), 1)
        _, _, vals = lines[0]
        self.assertEqual(vals["product_qty"], 2.0)
        # NetPrice 29.98 / qty 2 = 14.99 per unit
        self.assertAlmostEqual(vals["price_unit"], 14.99, places=2)
        self.assertEqual(vals["name"], "Schraubendreher Set")

    def test_empty_response_returns_no_lines(self):
        self.session.response = False
        self.assertEqual(self.session._prepare_purchase_order_lines(), [])

    @mute_logger("odoo.addons.punchout_ids_purchase.models.punchout_session")
    def test_malformed_xml_returns_no_lines(self):
        self.session.response = "not xml at all"
        self.assertEqual(self.session._prepare_purchase_order_lines(), [])

    def test_wrong_protocol_defers_to_super(self):
        self.backend.protocol = "cxml"
        self.session.response = IDS_CART
        self.assertEqual(self.session._prepare_purchase_order_lines(), [])

    def test_auto_creates_product(self):
        self.session.response = IDS_CART
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        product = self.env["product.product"].browse(vals["product_id"])
        self.assertTrue(product.exists())
        self.assertEqual(product.seller_ids.product_code, "ART-1")

    def test_post_create_product_hook_called_once_on_create(self):
        """_post_create_product_hook fires on auto-create; raw_data is
        the parsed IDS OrderItem element so overrides can pull
        IDS-specific fields (ArtNo, EAN, Langtext) without re-parsing."""
        from unittest.mock import patch

        self.session.response = IDS_CART
        with patch.object(
            type(self.session),
            "_post_create_product_hook",
            autospec=True,
        ) as hook:
            self.session._prepare_purchase_order_lines()
        self.assertEqual(hook.call_count, 1)
        _self, product, raw_data = hook.call_args[0]
        self.assertTrue(product.exists())
        self.assertEqual(str(raw_data.ArtNo), "ART-1")

    def test_post_create_product_hook_skipped_on_existing_match(self):
        from unittest.mock import patch

        self.env["product.product"].create(
            {
                "name": "Pre-existing IDS",
                "type": "consu",
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": self.partner.id,
                            "product_code": "ART-1",
                        },
                    )
                ],
            }
        )
        self.session.response = IDS_CART
        with patch.object(
            type(self.session),
            "_post_create_product_hook",
            autospec=True,
        ) as hook:
            self.session._prepare_purchase_order_lines()
        hook.assert_not_called()

    def test_no_match_does_not_graft_onto_unrelated_product(self):
        """The matching domain must not fall back to ``barcode = False`` —
        otherwise the IDS code would attach a new seller to the first
        barcode-less product it finds (typically a demo product), instead
        of auto-creating one."""
        # Pre-create a barcode-less product unrelated to our supplier; if
        # the domain were still permissive, the IDS code would graft
        # onto this product and add a second seller.
        unrelated = self.env["product.product"].create(
            {"name": "Unrelated barcode-less product", "type": "consu"}
        )
        sellers_before = len(unrelated.seller_ids)

        self.session.response = IDS_CART
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        created = self.env["product.product"].browse(vals["product_id"])

        self.assertNotEqual(
            created,
            unrelated,
            "IDS matching grafted onto an unrelated demo-shaped product "
            "instead of auto-creating a fresh one.",
        )
        self.assertEqual(len(unrelated.seller_ids), sellers_before)

    def test_no_auto_create_falls_back_to_existing_purchase_product(self):
        """auto_create_products=False: no matching product → fall back to
        any purchasable product, no creation."""
        self.backend.auto_create_products = False
        self.env["product.product"].create(
            {"name": "Fallback purchasable IDS", "type": "consu", "purchase_ok": True}
        )
        product_count_before = self.env["product.product"].search_count([])
        self.session.response = IDS_CART
        lines = self.session._prepare_purchase_order_lines()
        self.assertEqual(len(lines), 1)
        product_count_after = self.env["product.product"].search_count([])
        self.assertEqual(product_count_after, product_count_before)

    def test_ean_match_finds_existing_product(self):
        """When the IDS line carries an EAN that matches an existing
        product's barcode, that product is reused (not auto-created)."""
        existing = self.env["product.product"].create(
            {
                "name": "Pre-existing product with barcode",
                "type": "consu",
                "barcode": "4001234567890",
            }
        )
        cart_with_ean = IDS_CART.replace(
            "<NetPrice>29.98</NetPrice>",
            "<NetPrice>29.98</NetPrice>\n      <EAN>4001234567890</EAN>",
        )
        self.session.response = cart_with_ean
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        self.assertEqual(vals["product_id"], existing.id)

    def test_uom_mapping_is_used(self):
        dozen = self.env.ref("uom.product_uom_dozen")
        self.env["punchout.uom.mapping"].create(
            {
                "backend_id": self.backend.id,
                "supplier_code": "ST",
                "uom_id": dozen.id,
            }
        )
        self.session.response = IDS_CART
        lines = self.session._prepare_purchase_order_lines()
        _, _, vals = lines[0]
        self.assertEqual(vals["product_uom"], dozen.id)
