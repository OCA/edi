# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase

from odoo.addons.edi_oca.tests.common import EDIBackendTestMixin

from .common import OrderMixin


class TestOrderInbound(SavepointCase, EDIBackendTestMixin, OrderMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # force metadata storage w/ proper key
        cls.env = cls.env(context=dict(cls.env.context, edi_framework_action=True))
        cls.backend = cls._get_backend()
        cls.exc_type_in = cls.env.ref("edi_sale_ubl_oca.demo_edi_exc_type_order_in")
        cls.exc_record_in = cls.backend.create_record(
            cls.exc_type_in.code, {"edi_exchange_state": "input_received"}
        )
        cls._setup_order(
            origin_exchange_record_id=cls.exc_record_in.id,
            line_defaults=dict(origin_exchange_record_id=cls.exc_record_in.id),
        )

    @classmethod
    def _get_backend(cls):
        return cls.env.ref("edi_ubl_oca.edi_backend_ubl_demo")

    def test_state_accepted(self):
        order = self.sale
        self.assertEqual(order.edi_state_id.code, order.EDI_STATE_ORDER_ACCEPTED)
        self.assertTrue(
            order.mapped("order_line.edi_state_id").code,
            order.EDI_STATE_ORDER_LINE_ACCEPTED,
        )

    def test_state_partially_accepted(self):
        order = self.sale
        orig_qties = {}
        for line in order.order_line:
            orig_qties[line.id] = line.product_uom_qty
        line1, line2, line3 = order.order_line
        # change line 1
        line1.product_uom_qty = orig_qties[line1.id] - 1
        self.assertEqual(
            order.edi_state_id.code, order.EDI_STATE_ORDER_CONDITIONALLY_ACCEPTED
        )
        self.assertTrue(
            order.mapped("order_line.edi_state_id.code"),
            [
                order.EDI_STATE_ORDER_LINE_CHANGED,
                order.EDI_STATE_ORDER_LINE_ACCEPTED,
                order.EDI_STATE_ORDER_LINE_ACCEPTED,
            ],
        )
        # change line 2
        line2.product_uom_qty = orig_qties[line2.id] - 1
        self.assertEqual(
            order.edi_state_id.code, order.EDI_STATE_ORDER_CONDITIONALLY_ACCEPTED
        )
        self.assertTrue(
            order.mapped("order_line.edi_state_id.code"),
            [
                order.EDI_STATE_ORDER_LINE_CHANGED,
                order.EDI_STATE_ORDER_LINE_CHANGED,
                order.EDI_STATE_ORDER_LINE_ACCEPTED,
            ],
        )
        # change line 3
        line3.product_uom_qty = orig_qties[line3.id] - 1
        self.assertEqual(
            order.edi_state_id.code, order.EDI_STATE_ORDER_CONDITIONALLY_ACCEPTED
        )
        self.assertTrue(
            order.mapped("order_line.edi_state_id.code"),
            [
                order.EDI_STATE_ORDER_LINE_CHANGED,
                order.EDI_STATE_ORDER_LINE_CHANGED,
                order.EDI_STATE_ORDER_LINE_CHANGED,
            ],
        )
        # restore line 1
        line1.product_uom_qty = orig_qties[line1.id]
        self.assertEqual(
            order.edi_state_id.code, order.EDI_STATE_ORDER_CONDITIONALLY_ACCEPTED
        )
        self.assertTrue(
            order.mapped("order_line.edi_state_id.code"),
            [
                order.EDI_STATE_ORDER_LINE_ACCEPTED,
                order.EDI_STATE_ORDER_LINE_CHANGED,
                order.EDI_STATE_ORDER_LINE_CHANGED,
            ],
        )

    def test_state_rejected(self):
        order = self.sale
        order.action_cancel()
        self.assertEqual(order.edi_state_id.code, order.EDI_STATE_ORDER_REJECTED)

    def test_state_accepted_add_line(self):
        order = self.sale
        order.write({"state": "sale"})
        self.assertEqual(order.edi_state_id.code, order.EDI_STATE_ORDER_ACCEPTED)
        self.assertTrue(
            order.mapped("order_line.edi_state_id").code,
            order.EDI_STATE_ORDER_LINE_ACCEPTED,
        )
        lines = order.order_line
        order.write(
            {
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "product_uom_qty": 300,
                            "edi_id": 4000,
                            "origin_exchange_record_id": self.exc_record_in.id,
                        },
                    )
                ]
            }
        )
        new_line = order.order_line - lines
        self.assertEqual(
            new_line.edi_state_id.code, order.EDI_STATE_ORDER_LINE_ACCEPTED
        )
        new_line = order.order_line.create(
            {
                "order_id": order.id,
                "product_id": self.product_a.id,
                "product_uom_qty": 300,
                "edi_id": 4000,
                "origin_exchange_record_id": self.exc_record_in.id,
            }
        )
        self.assertEqual(
            new_line.edi_state_id.code, order.EDI_STATE_ORDER_LINE_ACCEPTED
        )
