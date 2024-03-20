# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import _, fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestDespatchAdviceImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.supplier = cls.env.ref("base.res_partner_12")
        cls.supplier.vat = "BE0477472701"
        cls.env.user.company_id.partner_id.vat = "BE0421801233"
        cls.product_1 = cls.env["product.product"].create(
            {
                "name": "Product 1",
                "default_code": "987654321",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "P1"})
                ],
            }
        )
        cls.product_2 = cls.env["product.product"].create(
            {
                "name": "Product 2",
                "default_code": "987654312",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "P2"})
                ],
            }
        )
        cls.product_3 = cls.env["product.product"].create(
            {
                "name": "Product 3",
                "default_code": "123456789",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "P3"})
                ],
            }
        )
        cls.product_4 = cls.env["product.product"].create(
            {
                "name": "Product 4",
                "default_code": "23456718",
                "seller_ids": [
                    (0, 0, {"partner_id": cls.supplier.id, "product_code": "P4"})
                ],
            }
        )
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.supplier.id,
                "date_order": fields.Datetime.now(),
                "date_planned": fields.Datetime.now(),
            }
        )
        cls.line1 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.product_1.id,
                "name": cls.product_1.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 24,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 15,
            }
        )
        cls.line2 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.product_2.id,
                "name": cls.product_2.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 5,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 25,
            }
        )

        cls.line3 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.product_3.id,
                "name": cls.product_3.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 15,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 25,
            }
        )

        cls.line4 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.product_4.id,
                "name": cls.product_4.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 15,
                "product_uom": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 25,
            }
        )
        cls.purchase_order.button_confirm()

        cls.DespatchAdviceImport = cls.env["despatch.advice.import"].create(
            {"document": base64.b64encode(bytes("<dummy></dummy>", "utf-8"))}
        )

    def order_line_to_data(self, order_line, qty=None, backorder_qty=None):
        return {
            "backorder_qty": backorder_qty,
            "qty": qty if qty is not None else order_line.product_qty,
            "order_line_id": order_line.id,
            "ref": order_line.order_id.name,
            "product_ref": order_line.product_id.default_code,
            "uom": {"unece_code": order_line.product_uom.unece_code},
        }

    def _get_base_data(self):
        return {
            "company": {"vat": "BE0421801233"},
            "date": "2020-02-04",
            "chatter_msg": [],
            "lines": [],
            "supplier": {"vat": "BE0477472701"},
            "ref": str(self.purchase_order.name),
        }

    def test_no_purchase_order_name(self):
        """
        Data:
            Data  with unknown PO reference
        Test Case:
            Process data
        Expected result:
            UserError is raised
        """
        data = self._get_base_data()
        data["ref"] = "123456"
        data["lines"] = [self.order_line_to_data(self.line1)]
        data["lines"][0]["ref"] = "123456"

        with self.assertRaises(UserError) as ue:
            self.DespatchAdviceImport.process_data(data)
        self.assertEqual(
            ue.exception.name, _("No purchase order found for name 123456.")
        )

    def test_process_data_with_backorder_qty(self):
        """
        backorder qty
        """
        data = self._get_base_data()
        confirmed_qty = self.line1.product_qty - 21
        data["lines"] = [
            self.order_line_to_data(self.line1, qty=confirmed_qty, backorder_qty=21),
            self.order_line_to_data(self.line2),
            self.order_line_to_data(self.line3),
            self.order_line_to_data(self.line4),
        ]
        self.DespatchAdviceImport.process_data(data)

        self.assertTrue(self.purchase_order.picking_ids)
        move_ids = self.line1.move_ids
        self.assertEqual(len(move_ids), 2)
        self.assertEqual(sum(move_ids.mapped("product_qty")), self.line1.product_qty)
        assigned = move_ids.filtered(lambda s: s.state == "done" and s.product_qty == 3)
        self.assertEqual(assigned.product_qty, confirmed_qty)

        move_backorder = move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 21
        )
        self.assertTrue(move_backorder)
        self.assertEqual(move_backorder.picking_id.backorder_id, assigned.picking_id)

    def test_process_data_with_no_backorder_qty(self):
        """
        no backorder qty
        """
        data = self._get_base_data()
        confirmed_qty = self.line1.product_qty - 21
        data["lines"] = [
            self.order_line_to_data(self.line1, qty=confirmed_qty),
            self.order_line_to_data(self.line2),
            self.order_line_to_data(self.line3),
            self.order_line_to_data(self.line4),
        ]
        self.DespatchAdviceImport.process_data(data)

        self.assertTrue(self.purchase_order.picking_ids)
        move_ids = self.line1.move_ids
        self.assertEqual(len(move_ids), 2)
        self.assertEqual(sum(move_ids.mapped("product_qty")), self.line1.product_qty)
        assigned = move_ids.filtered(lambda s: s.state == "done")
        self.assertEqual(assigned.product_qty, confirmed_qty)
        cancel = move_ids.filtered(lambda s: s.state == "cancel")
        self.assertEqual(cancel.product_qty, 21)

    def test_process_data_create_backorder(self):
        """
        2 back order created, second one is put in the same than the first 1
        """
        data = self._get_base_data()
        line1_confirmed_qty = self.line1.product_qty - 3
        line2_confirmed_qty = self.line2.product_qty - 3
        data["lines"] = [
            self.order_line_to_data(
                self.line1,
                qty=line1_confirmed_qty,
                backorder_qty=3,
            ),
            self.order_line_to_data(
                self.line2,
                qty=line2_confirmed_qty,
                backorder_qty=3,
            ),
            self.order_line_to_data(self.line3),
            self.order_line_to_data(self.line4),
        ]

        self.DespatchAdviceImport.process_data(data)
        self.assertEqual(self.purchase_order.state, "purchase")
        self.assertEqual(len(self.purchase_order.picking_ids), 2)
        # line1
        line1_move_ids = self.line1.move_ids
        self.assertEqual(len(line1_move_ids), 2)
        self.assertEqual(
            sum(line1_move_ids.mapped("product_qty")), self.line1.product_qty
        )
        move_confirmed = line1_move_ids.filtered(
            lambda s: s.state == "done" and s.product_qty == line1_confirmed_qty
        )
        self.assertTrue(move_confirmed)
        self.assertEqual(move_confirmed.product_qty, line1_confirmed_qty)
        move_backorder = line1_move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 3
        )
        self.assertTrue(move_backorder)
        self.assertEqual(
            move_backorder.picking_id.backorder_id,
            move_confirmed.picking_id,
        )

        # line2
        line2_move_ids = self.line2.move_ids
        self.assertEqual(len(line2_move_ids), 2)
        self.assertEqual(
            sum(line2_move_ids.mapped("product_qty")), self.line2.product_qty
        )
        move_confirmed = line2_move_ids.filtered(
            lambda s: s.state == "done" and s.product_qty == line2_confirmed_qty
        )
        self.assertTrue(move_confirmed)
        self.assertEqual(move_confirmed.product_qty, line2_confirmed_qty)

        move_backorder = line2_move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 3
        )
        self.assertTrue(move_backorder)
        self.assertEqual(
            move_backorder.picking_id.backorder_id,
            move_confirmed.picking_id,
        )

    def test_partial_delivery_with_backorder(self):
        """ """
        data = self._get_base_data()
        confirmed_qty = self.line1.product_qty - 3
        data["lines"] = [
            self.order_line_to_data(
                self.line1,
                qty=confirmed_qty,
                backorder_qty=2,
            ),
            self.order_line_to_data(self.line2),
            self.order_line_to_data(self.line3),
            self.order_line_to_data(self.line4),
        ]
        self.DespatchAdviceImport.process_data(data)
        self.assertEqual(len(self.purchase_order.picking_ids), 2)
        move_ids = self.line1.move_ids

        self.assertEqual(len(move_ids), 3)
        self.assertEqual(sum(move_ids.mapped("product_qty")), self.line1.product_qty)
        move_confirmed = move_ids.filtered(
            lambda s: s.state == "done" and s.product_qty == confirmed_qty
        )
        self.assertTrue(move_confirmed)
        move_cancel = move_ids.filtered(
            lambda s: s.state == "cancel" and s.product_qty == 1
        )
        self.assertTrue(move_cancel)
        move_backorder = move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 2
        )

        self.assertTrue(move_backorder)
        self.assertEqual(
            move_backorder.picking_id.backorder_id,
            move_confirmed.picking_id,
        )

    def test_qty_larger_backorder_qty(self):
        """ """
        data = self._get_base_data()
        confirmed_qty = 6
        data["lines"] = [
            self.order_line_to_data(self.line1),
            self.order_line_to_data(self.line2),
            self.order_line_to_data(self.line3, qty=confirmed_qty, backorder_qty=3),
            self.order_line_to_data(self.line4),
        ]
        self.DespatchAdviceImport.process_data(data)
        self.assertEqual(len(self.purchase_order.picking_ids), 2)
        move_ids = self.line3.move_ids
        self.assertEqual(len(move_ids), 3)
        self.assertEqual(sum(move_ids.mapped("product_qty")), self.line3.product_qty)
        moves_confirmed = move_ids.filtered(
            lambda s: s.state == "done" and not s.picking_id.backorder_id
        )
        self.assertEqual(sum(moves_confirmed.mapped("product_qty")), confirmed_qty)

        move_cancel = move_ids.filtered(
            lambda s: s.state == "cancel" and s.product_qty == 6
        )
        self.assertTrue(move_cancel)
        move_backorder = move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 3
        )
        self.assertTrue(move_backorder)
        self.assertEqual(
            move_backorder.picking_id.backorder_id,
            moves_confirmed[0].picking_id,
        )

    def test_qty_equal_backorder_qty(self):
        """ """
        data = self._get_base_data()
        confirmed_qty = 3
        data["lines"] = [
            self.order_line_to_data(self.line1),
            self.order_line_to_data(self.line2),
            self.order_line_to_data(self.line3),
            self.order_line_to_data(
                self.line4,
                qty=confirmed_qty,
                backorder_qty=3,
            ),
        ]
        self.DespatchAdviceImport.process_data(data)
        self.assertEqual(len(self.purchase_order.picking_ids), 2)
        move_ids = self.line4.move_ids
        self.assertEqual(sum(move_ids.mapped("product_qty")), self.line4.product_qty)
        moves_confirmed = move_ids.filtered(
            lambda s: s.state == "done" and not s.picking_id.backorder_id
        )
        self.assertEqual(sum(moves_confirmed.mapped("product_qty")), 3)

        moves_cancel = move_ids.filtered(
            lambda s: s.state == "cancel" and not s.picking_id.backorder_id
        )
        self.assertEqual(sum(moves_cancel.mapped("product_qty")), 9)
        moves_backorder = move_ids.filtered(
            lambda s: s.state == "assigned" and s.picking_id.backorder_id
        )
        self.assertEqual(sum(moves_backorder.mapped("product_qty")), 3)

    def test_confirmed_qty_larger_reserved_qty(self):
        """
        confirmed qty > reserved qty
        """
        data = self._get_base_data()
        confirmed_qty = self.line1.product_qty + 6
        data["lines"] = [
            self.order_line_to_data(self.line1, qty=confirmed_qty),
            self.order_line_to_data(self.line2),
            self.order_line_to_data(self.line3),
            self.order_line_to_data(self.line4),
        ]
        self.DespatchAdviceImport.with_context(
            allow_validate_over_qty=True
        ).process_data(data)

        self.assertTrue(self.purchase_order.picking_ids)
        move_ids = self.line1.move_ids
        self.assertEqual(len(move_ids), 1)
        self.assertEqual(sum(move_ids.mapped("product_qty")), confirmed_qty)
        assigned = move_ids.filtered(lambda s: s.state == "done")
        self.assertEqual(assigned.product_qty, confirmed_qty)
