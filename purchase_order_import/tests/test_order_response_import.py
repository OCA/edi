# -*- coding: utf-8 -*-
# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, _
from odoo.exceptions import UserError
from odoo.tests import SavepointCase

from ..wizard.order_response_import import (
    ORDER_RESPONSE_STATUS_ACK,
    ORDER_RESPONSE_STATUS_ACCEPTED,
    ORDER_RESPONSE_STATUS_REJECTED,
    ORDER_RESPONSE_STATUS_CONDITIONAL,
    LINE_STATUS_ACCEPTED,
    LINE_STATUS_REJECTED,
    LINE_STATUS_AMEND,
)


class TestOrderResponseImportCommon(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestOrderResponseImportCommon, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.supplier = cls.env.ref("base.res_partner_12")
        cls.supplier.vat = "BE0477472701"
        cls.env.user.company_id.partner_id.vat = "BE0421801233"
        cls.currency_euro = cls.env.ref("base.EUR")
        cls.currency_usd = cls.env.ref("base.USD")
        cls.product_1 = cls.env["product.product"].create(
            {
                "name": "Product 1",
                "seller_ids": [
                    (0, 0, {"name": cls.supplier.id, "product_code": "P1"})
                ],
            }
        )
        cls.product_2 = cls.env["product.product"].create(
            {
                "name": "Product 2",
                "seller_ids": [
                    (0, 0, {"name": cls.supplier.id, "product_code": "P2"})
                ],
            }
        )
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.supplier.id,
                "date_order": fields.Datetime.now(),
                "date_planned": fields.Datetime.now(),
                "currency_id": cls.currency_euro.id,
            }
        )
        cls.line1 = cls.purchase_order.order_line.create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.product_1.id,
                "name": cls.product_2.name,
                "date_planned": fields.Datetime.now(),
                "product_qty": 10,
                "product_uom": cls.env.ref("product.product_uom_unit").id,
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
                "product_uom": cls.env.ref("product.product_uom_unit").id,
                "price_unit": 25,
            }
        )
        cls.OrderResponseImport = cls.env["order.response.import"]
        cls.ProcurementOrder = cls.env["procurement.order"]

    def order_line_to_data(
        self,
        order_line,
        qty=None,
        status=LINE_STATUS_ACCEPTED,
        backorder_qty=None,
        note=None,
    ):
        return {
            "status": status,
            "backorder_qty": backorder_qty,
            "qty": qty if qty is not None else order_line.product_qty,
            "note": note,
            "line_id": str(order_line.id),
            "uom": {"unece_code": order_line.product_uom.unece_code},
        }

    def _add_procurements(self, line, qties):
        for qty in qties:
            self.ProcurementOrder.create(
                {
                    "name": "Test",
                    "product_id": line.product_id.id,
                    "product_qty": qty,
                    "product_uom": line.product_uom.id,
                    "state": "done",
                    "purchase_line_id": line.id,
                }
            )


class TestOrderResponseImport(TestOrderResponseImportCommon):
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

    def test_01(self):
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
        with self.assertRaises(UserError) as ue:
            self.OrderResponseImport.process_data(data)
        self.assertEqual(
            ue.exception.name, _("No purchase order found for name 123456.")
        )

    def test_02(self):
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
        self.assertEqual(ue.exception.name, _("Unknown status 'unknown'."))

    def test_03(self):
        """
        Data:
            Data with an other currency
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
            ue.exception.name,
            _(
                "The currency of the imported OrderResponse (USD) is "
                "different from the currency of the purchase order (EUR)."
            ),
        )

    def test_04(self):
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
        self.assertFalse(self.purchase_order.supplier_ack_dt)
        self.OrderResponseImport.process_data(data)
        self.assertTrue(self.purchase_order.supplier_ack_dt)

    def test_05(self):
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

    def test_06(self):
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

    def test_07(self):
        """
        Data:
            Data with status 'conditionally_accepted' and without lines
        Test Case:
            Process data
        Expected result:
            UserError is raised since a all line details must be provided with
            this status
        """
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_CONDITIONAL
        data["lines"] = []
        with self.assertRaises(UserError) as ue:
            self.OrderResponseImport.process_data(data)
            expected = (
                _(
                    "Unable to conditionally confirm the purchase order. \n"
                    "Line IDS into the parsed document differs from the "
                    "expected list of order line ids: \n "
                    "received: []\n"
                    "expected: %s\n"
                )
                % self.purchase_order.order_line.ids
            )
            self.assertEqual(ue.exception.name, expected)

    def test_08(self):
        """
        Data:
            Data with status 'conditionally_accepted' and with a wrong line id
        Test Case:
            Process data
        Expected result:
            UserError is raised since a all line details must be provided with
            this status
        """
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_CONDITIONAL
        data["lines"] = [self.order_line_to_data(self.line1)]
        line2 = self.order_line_to_data(self.line2)
        line2["line_id"] = "WRONG"
        data["lines"].append(line2)
        with self.assertRaises(UserError) as ue:
            self.OrderResponseImport.process_data(data)
            expected = _(
                "Unable to conditionally confirm the purchase order. \n"
                "Line IDS into the parsed document differs from the "
                "expected list of order line ids: \n "
                "received: [%s]\n"
                "expected: %s\n"
            ) % (
                [str(self.line1.id), "WRONG"],
                self.purchase_order.order_line.ids,
            )
            self.assertEqual(ue.exception.name, expected)

    def test_09(self):
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

    def test_10(self):
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
        self.assertEqual(self.line2.move_ids.note, "cancel by import")

    def test_11(self):
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
        self.assertEqual(self.line2.move_ids.note, "cancel by import")

    def test_12(self):
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
        self.assertEqual(
            sum(move_ids.mapped("product_qty")), self.line1.product_qty
        )
        assigned = move_ids.filtered(lambda s: s.state == "assigned")
        self.assertEqual(assigned.product_qty, confirmed_qty)
        cancel = move_ids.filtered(lambda s: s.state == "cancel")
        self.assertEqual(cancel.product_qty, 3)
        self.assertEqual(cancel.note, "No backorder planned by the supplier.")

    def test_13(self):
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
        self.assertEqual(
            sum(move_ids.mapped("product_qty")), self.line1.product_qty
        )
        move_confirmed = move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == confirmed_qty
        )
        self.assertTrue(move_confirmed)
        self.assertEqual(
            _("my note\n%s items should be delivered into a next delivery.")
            % "3.0",
            move_confirmed.note,
        )
        move_backorder = move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 3
        )
        self.assertTrue(move_backorder)
        self.assertEqual(
            move_backorder.picking_id.backorder_id, move_confirmed.picking_id,
        )

    def test_14(self):
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
            lambda s: s.state == "assigned"
            and s.product_qty == line1_confirmed_qty
        )
        self.assertTrue(move_confirmed)
        self.assertEqual(
            _("my note\n%s items should be delivered into a next delivery.")
            % "3.0",
            move_confirmed.note,
        )
        move_backorder = line1_move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 3
        )
        self.assertTrue(move_backorder)
        self.assertEqual(
            move_backorder.picking_id.backorder_id, move_confirmed.picking_id,
        )
        # lin1
        line2_move_ids = self.line2.move_ids
        self.assertEqual(len(line2_move_ids), 2)
        self.assertEqual(
            sum(line2_move_ids.mapped("product_qty")), self.line2.product_qty
        )
        move_confirmed = line2_move_ids.filtered(
            lambda s: s.state == "assigned"
            and s.product_qty == line2_confirmed_qty
        )
        self.assertTrue(move_confirmed)
        self.assertEqual(
            _("my note\n%s items should be delivered into a next delivery.")
            % "3.0",
            move_confirmed.note,
        )
        move_backorder = line2_move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 3
        )
        self.assertTrue(move_backorder)
        self.assertEqual(
            move_backorder.picking_id.backorder_id, move_confirmed.picking_id,
        )

    def test_15(self):
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
        self.assertEqual(
            sum(move_ids.mapped("product_qty")), self.line1.product_qty
        )
        move_confirmed = move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == confirmed_qty
        )
        self.assertTrue(move_confirmed)
        self.assertEqual(
            _("%s items should be delivered into a next delivery.") % "2.0",
            move_confirmed.note,
        )
        move_cancel = move_ids.filtered(
            lambda s: s.state == "cancel" and s.product_qty == 1
        )
        self.assertTrue(move_cancel)
        self.assertEqual(
            _("No backorder planned by the supplier."), move_cancel.note,
        )
        move_backorder = move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 2
        )
        self.assertTrue(move_backorder)
        self.assertEqual(
            move_backorder.picking_id.backorder_id, move_confirmed.picking_id,
        )

    def test_16(self):
        """
        Data:
            Sale order line:
            * line1 qty 10 linked to 1 procurement_order (qty into po 5)
            -> in such a case, the confirmation of the PO will create 2
                stock.move
                (1 for the procurement order and 1 for the remaining qty)
            Data with status 'conditionally_accepted'
            * line1 amended :
              * qty 6
              * backorder qty 3
            * line2 accepted
        Test Case:
            Process data
        Expected result:
            PO is confirmed
            One picking is created with four moves
            * line1 assigned with qty 5
            * line1 assigned with qty 1
            * line1 cancel with qty 1
            * line2 assigned with qty = confirmed qty
            One backorder picking is created with one move
            * line1 assigned with qty = 3
        """
        self._add_procurements(self.line1, [5])
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_CONDITIONAL
        confirmed_qty = 6
        data["lines"] = [
            self.order_line_to_data(
                self.line1,
                status=LINE_STATUS_AMEND,
                qty=confirmed_qty,
                backorder_qty=3,
            ),
            self.order_line_to_data(self.line2),
        ]
        self.OrderResponseImport.process_data(data)
        self.assertEqual(self.purchase_order.state, "purchase")
        self.assertEqual(len(self.purchase_order.picking_ids), 2)
        move_ids = self.line1.move_ids
        self.assertEqual(len(move_ids), 4)
        self.assertEqual(
            sum(move_ids.mapped("product_qty")), self.line1.product_qty
        )
        moves_confirmed = move_ids.filtered(
            lambda s: s.state == "assigned" and not s.picking_id.backorder_id
        )
        self.assertEqual(
            sum(moves_confirmed.mapped("product_qty")), confirmed_qty
        )

        self.assertIn(
            _("%s items should be delivered into a next delivery.") % "3.0",
            moves_confirmed.mapped("note"),
        )
        move_cancel = move_ids.filtered(
            lambda s: s.state == "cancel" and s.product_qty == 1
        )
        self.assertTrue(move_cancel)
        self.assertEqual(
            _("No backorder planned by the supplier."), move_cancel.note,
        )
        move_backorder = move_ids.filtered(
            lambda s: s.state == "assigned" and s.product_qty == 3
        )
        self.assertTrue(move_backorder)
        self.assertEqual(
            move_backorder.picking_id.backorder_id,
            moves_confirmed[0].picking_id,
        )

    def test_17(self):
        """
        Data:
            Sale order line:
            * line1 qty 10 linked to 4 procurement_order
            (qty into po (2, 2, 2, 2)))
             -> in such a case, the confirmation of the PO will create 5
                stock.move
                (1 one by procurement order and 1 for the remaining qty)
            Data with status 'conditionally_accepted'
            * line1 amended :
              * qty 3
              * backorder qty 3
            * line2 accepted
        Test Case:
            Process data
        Expected result:
            PO is confirmed
            One picking is created with four moves
            * sum(line1 cancel) 4
            * sum(line1 assigned) 3
            * line2 assigned with qty = confirmed qty
            One backorder picking is created with one move
            * sum(line1 assigned) 3
        """
        self._add_procurements(self.line1, [2, 2, 2])
        data = self._get_base_data()
        data["status"] = ORDER_RESPONSE_STATUS_CONDITIONAL
        confirmed_qty = 3
        data["lines"] = [
            self.order_line_to_data(
                self.line1,
                status=LINE_STATUS_AMEND,
                qty=confirmed_qty,
                backorder_qty=3,
            ),
            self.order_line_to_data(self.line2),
        ]
        self.OrderResponseImport.process_data(data)
        self.assertEqual(self.purchase_order.state, "purchase")
        self.assertEqual(len(self.purchase_order.picking_ids), 2)
        move_ids = self.line1.move_ids
        self.assertEqual(
            sum(move_ids.mapped("product_qty")), self.line1.product_qty
        )
        moves_confirmed = move_ids.filtered(
            lambda s: s.state == "assigned" and not s.picking_id.backorder_id
        )
        self.assertEqual(sum(moves_confirmed.mapped("product_qty")), 3)

        moves_cancel = move_ids.filtered(
            lambda s: s.state == "cancel" and not s.picking_id.backorder_id
        )
        self.assertEqual(sum(moves_cancel.mapped("product_qty")), 4)
        moves_backorder = move_ids.filtered(
            lambda s: s.state == "assigned" and s.picking_id.backorder_id
        )
        self.assertEqual(sum(moves_backorder.mapped("product_qty")), 3)
