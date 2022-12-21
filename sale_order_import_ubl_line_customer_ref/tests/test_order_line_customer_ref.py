# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import SavepointCase


class TestOrderLineCustomerRef(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test customer_ref 1",
                "barcode": "prod1",
            }
        )
        cls.product2 = cls.env["product.product"].create(
            {
                "name": "Test customer_ref 2",
                "barcode": "prod2",
            }
        )
        cls.customer_ref1 = "#customer1"
        cls.customer_ref2 = "#customer2"
        cls.customer_ref3 = "#customer3"
        cls.parsed_order = {
            "partner": {"email": "johnny.glamour@example.com"},
            "lines": [
                {
                    "product": {"barcode": "prod1"},
                    "qty": 1,
                    "uom": {"unece_code": "C62"},
                    "note": "customer_ref: " + cls.customer_ref1,
                },
                {
                    "product": {"barcode": "prod1"},
                    "qty": 1,
                    "uom": {"unece_code": "C62"},
                    "note": "customer_ref: " + cls.customer_ref2,
                },
                {
                    "product": {"barcode": "prod2"},
                    "qty": 4,
                    "uom": {"unece_code": "C62"},
                    "note": "customer_ref: " + cls.customer_ref3,
                },
            ],
            "chatter_msg": [],
            "doc_type": "rfq",
        }
        cls.soi = cls.env["sale.order.import"]

    def test_customer_ref_parsing(self):
        self.assertEqual(self.soi._get_order_line_customer_ref({}), "")
        self.assertEqual(self.soi._get_order_line_customer_ref({"note": ""}), "")
        self.assertEqual(self.soi._get_order_line_customer_ref({"note": "bla bla"}), "")
        self.assertEqual(
            self.soi._get_order_line_customer_ref({"note": "customer_ref:abc"}), "abc"
        )
        self.assertEqual(
            self.soi._get_order_line_customer_ref(
                {"note": "bla bla\ncustomer_ref:abc"}
            ),
            "abc",
        )

    def test_order_line_customer_ref(self):
        order = self.soi.create_order(self.parsed_order, "pricelist")
        for i, line in enumerate(order.order_line, start=1):
            self.assertEqual(line.customer_ref, getattr(self, f"customer_ref{i}"))
