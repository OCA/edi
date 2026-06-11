# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from odoo.addons.purchase_order_import.wizard.purchase_order_response_import import (
    LINE_STATUS_AMEND,
    LINE_STATUS_REJECTED,
    ORDER_RESPONSE_STATUS_ACCEPTED,
    ORDER_RESPONSE_STATUS_ACK,
    ORDER_RESPONSE_STATUS_CONDITIONAL,
    ORDER_RESPONSE_STATUS_REJECTED,
)

from .common import TestPurchaseOrderResponseImportCommon


class TestPurchaseOrderResponseImport(TestPurchaseOrderResponseImportCommon):
    def _get_base_data(self):
        return {
            "status": ORDER_RESPONSE_STATUS_ACK,
            "company": {"vat": "BE0421801233"},
            "currency": {"iso": "EUR"},
            "date": "2020-02-04",
            "chatter_msg": [],
            "lines": [],
            "note": "Note1\nNote2",
            "time": "22:10:30",
            "supplier": {"vat": "BE0477472701"},
            "ref": str(self.purchase_order.name),
        }

    def test_01_unknown_po_ref(self):
        """
        Data:
            Data with unknown PO reference
        Test Case:
            Process data
        Expected result:
            UserError is raised
        """
        data = self._get_base_data()
        data["ref"] = "123456"
        with self.assertRaises(UserError) as ue:
            self.OrderResponseImport.process_data(data)
        self.assertEqual(
            ue.exception.args[0], "No purchase order found for name 123456."
        )

    def test_02_unknown_po_status(self):
        """
        Data:
            Data with unknown PO status
        Test Case:
            Process data
        Expected result:
            UserError is raised
        """
        data = self._get_base_data()
        data["status"] = "unknown"
        with self.assertRaises(UserError) as ue:
            self.OrderResponseImport.process_data(data)
        self.assertEqual(ue.exception.args[0], "Unknown status 'unknown'.")

    def test_03_different_po_currency(self):
        """
        Data:
            Data with another currency
        Test Case:
            Process data
        Expected result:
            UserError is raised
        """
        data = self._get_base_data()
        data["currency"] = {"iso": self.currency_usd.name}
        with self.assertRaises(UserError) as ue:
            self.OrderResponseImport.process_data(data)
        self.assertEqual(
            ue.exception.args[0],
            "The currency of the imported OrderResponse (USD) is different from the"
            " currency of the purchase order (EUR).",
        )

    def test_04_receive_ack_status(self):
        """
        Data:
            Data with status ack.
        Test Case:
            Process data
        Expected result:
            The ack info is filled
        """
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_ACK
        self.assertFalse(self.purchase_order.supplier_ack_received_on)
        self.OrderResponseImport.process_data(data)
        self.assertTrue(self.purchase_order.supplier_ack_received_on)

    def test_05_receive_accepted_status(self):
        """
        Data:
            Data with status accepted
            PO not yet confirmed
        Test Case:
            Process data
        Expected result:
            PO is confirmed
            A picking is created
        """
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_ACCEPTED
        self.assertFalse(self.purchase_order.picking_ids)
        self.assertEqual(self.purchase_order.state, "draft")
        self.OrderResponseImport.process_data(data)
        self.assertTrue(self.purchase_order.picking_ids)
        self.assertEqual(self.purchase_order.state, "purchase")

    def test_06_receive_rejected_status(self):
        """
        Data:
            Data with status rejected
            PO not yet confirmed
        Test Case:
            Process data
        Expected result:
            PO is cancelled
        """
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_REJECTED
        self.assertEqual(self.purchase_order.state, "draft")
        self.OrderResponseImport.process_data(data)
        self.assertEqual(self.purchase_order.state, "cancel")

    def test_07_receive_conditionally_accepted_status_without_lines(self):
        """
        Data:
            Data with status 'conditionally_accepted' and without lines
        Test Case:
            Process data
        Expected result:
            UserError is raised since all line details must be provided with this status
        """
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_CONDITIONAL
        data["lines"] = []
        with self.assertRaises(UserError) as ue:
            self.OrderResponseImport.process_data(data)
            expected = (
                "Unable to conditionally confirm the purchase order. \n"
                "Line IDS into the parsed document differs from the "
                "expected list of order line ids: \n "
                "received: []\n"
                "expected: %s\n",
                self.purchase_order.order_line.ids,
            )
            self.assertEqual(ue.exception.args[0], expected)

    def test_08_receive_conditionally_accepted_status_with_wrong_line_id(self):
        """
        Data:
            Data with status 'conditionally_accepted' and with a wrong line id
        Test Case:
            Process data
        Expected result:
            UserError is raised since all line details must be provided with this status
        """
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_CONDITIONAL
        data["lines"] = [self.order_line_to_data(self.line1)]
        line2 = self.order_line_to_data(self.line2)
        line2["line_id"] = "WRONG"
        data["lines"].append(line2)
        with self.assertRaises(UserError) as ue:
            self.OrderResponseImport.process_data(data)
            expected = (
                "Unable to conditionally confirm the purchase order. \n"
                "Line IDS into the parsed document differs from the "
                "expected list of order line ids: \n "
                "received: [%s]\n"
                "expected: %s\n",
                [str(self.line1.id), "WRONG"],
                self.purchase_order.order_line.ids,
            )
            self.assertEqual(ue.exception.args[0], expected)

    def test_09_receive_conditionally_accepted_status_all_lines_accepted(self):
        """
        Data:
            Data with status 'conditionally_accepted' and all line accepted
        Test Case:
            Process data
        Expected result:
            PO is confirmed
            A picking is created with one move by po line in state assigned
        """
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_CONDITIONAL
        data["lines"] = [
            self.order_line_to_data(self.line1),
            self.order_line_to_data(self.line2),
        ]
        self.OrderResponseImport.process_data(data)
        self.assertEqual(self.purchase_order.state, "purchase")
        self.assertTrue(self.purchase_order.picking_ids)
        self.assertEqual(self.line1.move_ids.state, "assigned")
        self.assertEqual(self.line2.move_ids.state, "assigned")

    def test_10_receive_conditionally_accepted_status_mixed_lines_statuses(self):
        """
        Data:
            Data with status 'conditionally_accepted' and one line accepted
            and another one rejected
        Test Case:
            Process data
        Expected result:
            PO is confirmed
            A picking is created with one move by po line
            The move linked to the accepted line is in state assigned
            The move linked to the rejected line is in state cancel
        """
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_CONDITIONAL
        data["lines"] = [
            self.order_line_to_data(self.line1),
            self.order_line_to_data(
                self.line2,
                status=LINE_STATUS_REJECTED,
                note="cancel by import",
            ),
        ]
        self.OrderResponseImport.process_data(data)
        self.assertEqual(self.purchase_order.state, "purchase")
        self.assertTrue(self.purchase_order.picking_ids)
        self.assertEqual(self.line1.move_ids.state, "assigned")
        self.assertEqual(self.line2.move_ids.state, "cancel")
        self.assertIn("cancel by import", self.line2.move_ids.description_picking)

    def test_11_receive_conditionally_accepted_status_mixed_lines_statuses(self):
        """
        Data:
            Data with status 'conditionally_accepted'
            * line1 amended with less qty than ordered and without
              backorder qty
            * line2 accepted
        Test Case:
            Process data
        Expected result:
            PO is confirmed
            A picking is created with two moves for the amended line
            * line1 move 1 assigned with qty = confirmed qty
            * line1 move 2 cancel with qty = expected qty -confirmed qty
        """
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_CONDITIONAL
        confirmed_qty = self.line1.product_qty - 3
        data["lines"] = [
            self.order_line_to_data(
                self.line1, status=LINE_STATUS_AMEND, qty=confirmed_qty
            ),
            self.order_line_to_data(self.line2),
        ]
        self.OrderResponseImport.process_data(data)
        self.assertEqual(self.purchase_order.state, "purchase")
        self.assertTrue(self.purchase_order.picking_ids)
        move_ids = self.line1.move_ids
        self.assertEqual(len(move_ids), 2)
        self.assertEqual(sum(move_ids.mapped("product_qty")), self.line1.product_qty)
        assigned = move_ids.filtered(lambda s: s.state == "assigned")
        self.assertEqual(assigned.product_qty, confirmed_qty)
        cancel = move_ids.filtered(lambda s: s.state == "cancel")
        self.assertEqual(cancel.product_qty, 3)
        self.assertIn(
            "No backorder planned by the supplier.", cancel.description_picking
        )

    def test_12_receive_conditionally_accepted_status_mixed_lines_statuses(self):
        """
        Data:
            Data with status 'conditionally_accepted'
            * line1 amended with less qty than ordered and with
              backorder qty equal to remaining qty
            * line2 accepted
        Test Case:
            Process data
        Expected result:
            PO is confirmed
            One picking is created with two moves
            * line1 assigned with qty = confirmed qty
            * line2 assigned with qty = confirmed qty
            One backorder picking is created with one move
            * line1 assigned with qty = expected qty - confirmed qty
        """
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_CONDITIONAL
        confirmed_qty = self.line1.product_qty - 3
        data["lines"] = [
            self.order_line_to_data(
                self.line1,
                status=LINE_STATUS_AMEND,
                qty=confirmed_qty,
                backorder_qty=3,
                note="my note",
            ),
            self.order_line_to_data(self.line2),
        ]
        self.OrderResponseImport.process_data(data)
        self.assertEqual(self.purchase_order.state, "purchase")
        self.assertEqual(len(self.purchase_order.picking_ids), 2)
        move_ids = self.line1.move_ids
        self.assertEqual(len(move_ids), 2)
        self.assertEqual(sum(move_ids.mapped("product_qty")), self.line1.product_qty)
        move_confirmed = move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == confirmed_qty
        )
        self.assertTrue(move_confirmed)
        self.assertIn(
            "3 items should be delivered into a next delivery.",
            move_confirmed.description_picking,
        )
        move_backorder = move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 3
        )
        self.assertTrue(move_backorder)
        self.assertEqual(
            move_backorder.picking_id.backorder_id,
            move_confirmed.picking_id,
        )

    def test_13_receive_conditionally_accepted_status_all_lines_amended(self):
        """
        Data:
            Data with status 'conditionally_accepted'
            * line1 amended with less qty than ordered and with
              backorder qty equal to remaining qty
            * line2 amended with less qty than ordered and with
              backorder qty equal to remaining qty
        Test Case:
            Process data
        Expected result:
            PO is confirmed
            One picking is created with two moves
            * line1 assigned with qty = confirmed qty
            * line2 assigned with qty = confirmed qty
            One backorder picking is created with two moves
            * line1 assigned with qty = expected qty - confirmed qty
            * line2 assigned with qty = expected qty - confirmed qty
        """
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_CONDITIONAL
        line1_confirmed_qty = self.line1.product_qty - 3
        line2_confirmed_qty = self.line2.product_qty - 3
        data["lines"] = [
            self.order_line_to_data(
                self.line1,
                status=LINE_STATUS_AMEND,
                qty=line1_confirmed_qty,
                backorder_qty=3,
                note="my note",
            ),
            self.order_line_to_data(
                self.line2,
                status=LINE_STATUS_AMEND,
                qty=line2_confirmed_qty,
                backorder_qty=3,
                note="my note",
            ),
        ]
        self.OrderResponseImport.process_data(data)
        self.assertEqual(self.purchase_order.state, "purchase")
        self.assertEqual(len(self.purchase_order.picking_ids), 2)
        # line1
        line1_move_ids = self.line1.move_ids
        self.assertEqual(len(line1_move_ids), 2)
        self.assertEqual(
            sum(line1_move_ids.mapped("product_qty")), self.line1.product_qty
        )
        move_confirmed = line1_move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == line1_confirmed_qty
        )
        self.assertTrue(move_confirmed)
        self.assertIn(
            "3 items should be delivered into a next delivery.",
            move_confirmed.description_picking,
        )
        move_backorder = line1_move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 3
        )
        self.assertTrue(move_backorder)
        self.assertEqual(
            move_backorder.picking_id.backorder_id,
            move_confirmed.picking_id,
        )
        # lin1
        line2_move_ids = self.line2.move_ids
        self.assertEqual(len(line2_move_ids), 2)
        self.assertEqual(
            sum(line2_move_ids.mapped("product_qty")), self.line2.product_qty
        )
        move_confirmed = line2_move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == line2_confirmed_qty
        )
        self.assertTrue(move_confirmed)
        self.assertIn(
            "3 items should be delivered into a next delivery.",
            move_confirmed.description_picking,
        )
        move_backorder = line2_move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 3
        )
        self.assertTrue(move_backorder)
        self.assertEqual(
            move_backorder.picking_id.backorder_id,
            move_confirmed.picking_id,
        )

    def test_14_receive_conditionally_accepted_status_mixed_lines_statuses(self):
        """
        Data:
            Data with status 'conditionally_accepted'
            * line1 amended with less qty than ordered and with
              backorder qty less than the remaining qty
            * line2 accepted
        Test Case:
            Process data
        Expected result:
            PO is confirmed
            One picking is created with three moves
            * line1 assigned with qty = confirmed qty
            * line1 cancel with qty = qty that will not be delivered
            * line2 assigned with qty = confirmed qty
            One backorder picking is created with one move
            * line1 assigned with qty = planned backorder qty
        """
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_CONDITIONAL
        confirmed_qty = self.line1.product_qty - 3
        data["lines"] = [
            self.order_line_to_data(
                self.line1,
                status=LINE_STATUS_AMEND,
                qty=confirmed_qty,
                backorder_qty=2,
            ),
            self.order_line_to_data(self.line2),
        ]
        self.OrderResponseImport.process_data(data)
        self.assertEqual(self.purchase_order.state, "purchase")
        self.assertEqual(len(self.purchase_order.picking_ids), 2)
        move_ids = self.line1.move_ids
        self.assertEqual(len(move_ids), 3)
        self.assertEqual(sum(move_ids.mapped("product_qty")), self.line1.product_qty)
        move_confirmed = move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == confirmed_qty
        )
        self.assertTrue(move_confirmed)
        self.assertIn(
            "2 items should be delivered into a next delivery.",
            move_confirmed.description_picking,
        )
        move_cancel = move_ids.filtered(
            lambda s: s.state == "cancel" and s.product_qty == 1
        )
        self.assertTrue(move_cancel)
        self.assertIn(
            "No backorder planned by the supplier.",
            move_cancel.description_picking,
        )
        move_backorder = move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 2
        )
        self.assertTrue(move_backorder)
        self.assertEqual(
            move_backorder.picking_id.backorder_id,
            move_confirmed.picking_id,
        )
