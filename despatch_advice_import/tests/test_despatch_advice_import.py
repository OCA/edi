# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo.exceptions import UserError

from .common import TestDespatchAdviceImportCommon


class TestDespatchAdviceImport(TestDespatchAdviceImportCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_1 = cls._create_product("Product 1", "987654321", "P1")
        cls.product_2 = cls._create_product("Product 2", "987654312", "P2")
        cls.product_3 = cls._create_product("Product 3", "123456789", "P3")
        cls.product_4 = cls._create_product("Product 4", "23456718", "P4")
        cls.purchase_order = cls._create_purchase_order(
            [
                cls._get_po_line_vals(cls.product_1, 24, 15),
                cls._get_po_line_vals(cls.product_2, 5, 25),
                cls._get_po_line_vals(cls.product_3, 15, 25),
                cls._get_po_line_vals(cls.product_4, 15, 25),
            ]
        )
        cls.line1, cls.line2, cls.line3, cls.line4 = cls.purchase_order.order_line
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
            "uom": {"unece_code": order_line.product_uom_id.unece_code},
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
        """Raise an error when the imported line references an unknown PO."""
        data = self._get_base_data()
        data["ref"] = "123456"
        data["lines"] = [self.order_line_to_data(self.line1)]
        data["lines"][0]["ref"] = "123456"

        with self.assertRaises(UserError) as ue:
            self.DespatchAdviceImport.process_data(data)
        self.assertEqual(
            ue.exception.args[0],
            self.env._("No purchase order found for name %(name)s.", name="123456"),
        )

    def test_process_data_with_backorder_qty(self):
        """Split the move and keep the postponed quantity on a backorder."""
        data = self._get_base_data()
        confirmed_qty = self.line1.product_qty - 21
        data["lines"] = [
            self.order_line_to_data(self.line1, qty=confirmed_qty, backorder_qty=21),
            self.order_line_to_data(self.line2),
            self.order_line_to_data(self.line3),
            self.order_line_to_data(self.line4),
        ]
        self.DespatchAdviceImport.with_context(
            despatch_advice_import__picking_validation=True
        ).process_data(data)

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
        """Split the move and cancel the remaining quantity without backorder."""
        data = self._get_base_data()
        confirmed_qty = self.line1.product_qty - 21
        data["lines"] = [
            self.order_line_to_data(self.line1, qty=confirmed_qty),
            self.order_line_to_data(self.line2),
            self.order_line_to_data(self.line3),
            self.order_line_to_data(self.line4),
        ]
        self.DespatchAdviceImport.with_context(
            despatch_advice_import__picking_validation=True
        ).process_data(data)

        self.assertTrue(self.purchase_order.picking_ids)
        move_ids = self.line1.move_ids
        self.assertEqual(len(move_ids), 2)
        self.assertEqual(sum(move_ids.mapped("product_qty")), self.line1.product_qty)
        assigned = move_ids.filtered(lambda s: s.state == "done")
        self.assertEqual(assigned.product_qty, confirmed_qty)
        cancel = move_ids.filtered(lambda s: s.state == "cancel")
        self.assertEqual(cancel.product_qty, 21)

    def test_process_data_create_backorder(self):
        """Reuse the same backorder picking for postponed quantities on two lines."""
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

        self.DespatchAdviceImport.with_context(
            despatch_advice_import__picking_validation=True
        ).process_data(data)
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
        """Backorder only the postponed part and cancel the leftover remainder."""
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
        self.DespatchAdviceImport.with_context(
            despatch_advice_import__picking_validation=True
        ).process_data(data)
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
        """Cancel the extra remainder when confirmed quantity exceeds backorder qty."""
        data = self._get_base_data()
        confirmed_qty = 6
        data["lines"] = [
            self.order_line_to_data(self.line1),
            self.order_line_to_data(self.line2),
            self.order_line_to_data(self.line3, qty=confirmed_qty, backorder_qty=3),
            self.order_line_to_data(self.line4),
        ]
        self.DespatchAdviceImport.with_context(
            despatch_advice_import__picking_validation=True
        ).process_data(data)
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
        """Keep equal confirmed and backorder quantities and cancel the rest."""
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
        self.DespatchAdviceImport.with_context(
            despatch_advice_import__picking_validation=True
        ).process_data(data)
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
        """Allow over-delivery when the imported confirmed quantity exceeds reserved."""
        data = self._get_base_data()
        confirmed_qty = self.line1.product_qty + 6
        data["lines"] = [
            self.order_line_to_data(self.line1, qty=confirmed_qty),
            self.order_line_to_data(self.line2),
            self.order_line_to_data(self.line3),
            self.order_line_to_data(self.line4),
        ]
        self.DespatchAdviceImport.with_context(
            allow_validate_over_qty=True,
            despatch_advice_import__picking_validation=True,
        ).process_data(data)

        self.assertTrue(self.purchase_order.picking_ids)
        move_ids = self.line1.move_ids
        self.assertEqual(len(move_ids), 1)
        self.assertEqual(sum(move_ids.mapped("product_qty")), self.line1.product_qty)
        assigned = move_ids.filtered(lambda s: s.state == "done")
        self.assertEqual(assigned.quantity, confirmed_qty)

    def test_process_data_without_picking_validation(self):
        """Leave the picking open when picking validation is not opted in."""
        data = self._get_base_data()
        data["lines"] = [
            self.order_line_to_data(self.line1),
            self.order_line_to_data(self.line2),
            self.order_line_to_data(self.line3),
            self.order_line_to_data(self.line4),
        ]
        self.DespatchAdviceImport.process_data(data)

        self.assertEqual(len(self.purchase_order.picking_ids), 1)
        picking = self.purchase_order.picking_ids
        self.assertEqual(picking.state, "assigned")
        move_ids = picking.move_ids
        self.assertTrue(move_ids)
        self.assertTrue(all(state == "assigned" for state in move_ids.mapped("state")))
        self.assertFalse(any(move_ids.mapped("picked")))
