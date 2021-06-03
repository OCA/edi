# Copyright 2018 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestOrderImport(TransactionCase):
    def test_order_import(self):
        soio = self.env["sale.order.import"]
        parsed_order = {
            "partner": {"email": "deco.addict82@example.com"},
            "date": "2018-08-14",
            "order_ref": "TEST1242",
            "lines": [
                {
                    "product": {"code": "FURN_8888"},
                    "qty": 2,
                    "uom": {"unece_code": "C62"},
                    "price_unit": 12.42,
                }
            ],
            "chatter_msg": [],
            "doc_type": "rfq",
        }
        order = soio.create_order(parsed_order, "pricelist")
        self.assertEqual(order.client_order_ref, parsed_order["order_ref"])
        self.assertEqual(
            order.order_line[0].product_id.default_code,
            parsed_order["lines"][0]["product"]["code"],
        )
        self.assertEqual(int(order.order_line[0].product_uom_qty), 2)
        # Now update the order
        parsed_order_up = {
            "partner": {"email": "agrolait@yourcompany.example.com"},
            "date": "2018-08-14",
            "order_ref": "TEST1242",
            "lines": [
                {
                    "product": {"code": "FURN_8888"},
                    "qty": 3,
                    "uom": {"unece_code": "C62"},
                    "price_unit": 12.42,
                },
                {
                    "product": {"code": "FURN_9999"},
                    "qty": 1,
                    "uom": {"unece_code": "C62"},
                    "price_unit": 1.42,
                },
            ],
            "chatter_msg": [],
            "doc_type": "rfq",
        }
        soio.update_order_lines(parsed_order_up, order, "pricelist")
        self.assertEqual(len(order.order_line), 2)
        self.assertEqual(int(order.order_line[0].product_uom_qty), 3)
