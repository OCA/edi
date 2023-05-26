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
        order._edi_update_state()
        self.assertEqual(order.edi_state_id.code, order.EDI_STATE_ORDER_ACCEPTED)
        self.assertTrue(
            order.mapped("order_line.edi_state_id").code,
            order.EDI_STATE_ORDER_LINE_ACCEPTED,
        )

    def test_state_partially_accepted(self):
        order = self.sale
        order.order_line[0].product_uom_qty = order.order_line[0].product_uom_qty - 1
        order._edi_update_state()
        self.assertEqual(
            order.edi_state_id.code, order.EDI_STATE_ORDER_CONDITIONALLY_ACCEPTED
        )
        self.assertTrue(
            order.mapped("order_line.edi_state_id").code,
            order.EDI_STATE_ORDER_LINE_CHANGED,
        )

    def test_state_rejected(self):
        order = self.sale
        order.action_cancel()
        order._edi_update_state()
        self.assertEqual(order.edi_state_id.code, order.EDI_STATE_ORDER_REJECTED)
