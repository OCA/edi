# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import SingleTransactionCase


class TestSaleOrderCustomerFreeRef(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.order = cls.env.ref("sale.sale_order_1")

    def test_client_order_ref_computation(self):
        self.order.customer_order_number = "123"
        self.order.customer_order_free_ref = ""
        self.assertEqual(self.order.client_order_ref, "123")
        self.order.customer_order_free_ref = "MrPink"
        self.assertEqual(self.order.client_order_ref, "123 - MrPink")
        self.order.action_confirm()
        for line in self.order.order_line:
            line.qty_delivered = line.product_uom_qty
        invoice = self.order._create_invoices()
        self.assertTrue(invoice)
        self.assertEqual(
            self.order.customer_order_number, invoice.customer_order_number
        )
        self.assertEqual(
            self.order.customer_order_free_ref, invoice.customer_order_free_ref
        )
        self.assertEqual(self.order.client_order_ref, invoice.ref)

    def test_client_order_ref_computation_empty_values(self):
        self.order.customer_order_number = "123"
        self.order.customer_order_free_ref = "  "
        self.assertEqual(self.order.client_order_ref, "123")
        self.order.customer_order_number = ""
        self.order.customer_order_free_ref = "MrPink"
        self.assertEqual(self.order.client_order_ref, "MrPink")

    def test_client_order_ref_inverse_function(self):
        self.order.client_order_ref = "456 - MrBlue"
        self.assertEqual(self.order.customer_order_number, "456")
        self.assertEqual(self.order.customer_order_free_ref, "MrBlue")
        self.order.client_order_ref = "456/abc"
        self.assertEqual(self.order.customer_order_number, "456/abc")
        self.assertFalse(self.order.customer_order_free_ref)
        self.order.client_order_ref = ""
        self.assertFalse(self.order.customer_order_number)
        self.assertFalse(self.order.customer_order_free_ref)
