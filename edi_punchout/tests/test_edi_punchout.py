# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree, objectify

from odoo.tests.common import Form, TransactionCase


class TestEdiPunchout(TransactionCase):
    def setUp(self):
        super().setUp()
        self.ids_account = self.env.ref("edi_punchout.edi_punchout_account_ids")
        self.oci_account = self.env.ref("edi_punchout.edi_punchout_account_oci")
        self.product = self.env["product.product"].create(
            {
                "name": "Punchout test product",
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.ids_account.partner_id.id,
                            "product_code": "424242",
                        },
                    )
                ],
            }
        )
        with Form(self.env["purchase.order"]) as po_form:
            po_form.partner_id = self.ids_account.partner_id
            with po_form.order_line.new() as order_line_form:
                order_line_form.product_id = self.product

            self.purchase_order = po_form.save()

    def test_ids(self):
        """Test an IDS roundtrip"""
        cart = etree.fromstring(
            self.env.ref("edi_punchout.ids_send_cart").render(
                {"object": self.purchase_order, "account": self.ids_account}
            )
        )
        ns = dict(w="http://www.itek.de/Shop-Anbindung/Warenkorb/")
        for order_item in cart.xpath("//w:OrderItem", namespaces=ns):
            etree.SubElement(order_item, "NetPrice").text = "42"
            etree.SubElement(order_item, "Kurztext").text = "short text"
            etree.SubElement(order_item, "Langtext").text = "long text"
            etree.SubElement(order_item, "VAT").text = "42"
        cart_xml = etree.tostring(cart).decode("utf8")
        new_purchase_order = self.ids_account._handle_return(
            cart_xml, order=self.purchase_order
        )
        self.assertEqual(
            self.purchase_order.order_line.product_id,
            new_purchase_order.order_line.product_id,
        )
        new_purchase_order.mapped("order_line.product_id.seller_ids").unlink()
        another_purchase_order = self.ids_account._handle_return(cart_xml)
        self.assertEqual(
            another_purchase_order.order_line.product_id.seller_ids.product_code,
            "424242",
        )
        another_purchase_order.button_approve()
        self.assertEqual(another_purchase_order.state, "ids_send")

    def test_ids_alternative_uom(self):
        """
        Test that we find an UOM with the wrong name when we set it as alternative name
        """
        order_item = objectify.fromstring("<OrderItem><QU>unknown_uom</QU></OrderItem>")
        uom = self.env.ref("uom.product_uom_meter")
        uom.ids_name_alternative = False
        self.assertEqual(
            self.ids_account._ids_get_or_create_uom(order_item),
            self.env.ref("uom.product_uom_unit"),
        )
        uom.ids_name_alternative = "unknown_uom"
        self.assertEqual(self.ids_account._ids_get_or_create_uom(order_item), uom)
        uom.ids_name_alternative = "some_other_uom unknown_uom"
        self.assertEqual(self.ids_account._ids_get_or_create_uom(order_item), uom)
        uom.ids_name_alternative = "some_other_uom unknown_uom and another"
        self.assertEqual(self.ids_account._ids_get_or_create_uom(order_item), uom)
        uom.ids_name_alternative = "unknown_uom and another"
        self.assertEqual(self.ids_account._ids_get_or_create_uom(order_item), uom)

    def test_oci(self):
        """Test an OCI roundtrip"""
        new_purchase_order = self.oci_account._handle_return(
            [
                {
                    "QUANTITY": 1,
                    "PRICE": 42,
                    "DESCRIPTION": "testproduct",
                    "VENDORMAT": "424242",
                }
            ]
        )
        self.assertEqual(
            new_purchase_order.order_line.product_id, self.product,
        )
