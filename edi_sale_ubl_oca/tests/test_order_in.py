# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import exceptions
from odoo.tests.common import SavepointCase

from odoo.addons.component.tests.common import ComponentMixin
from odoo.addons.edi_oca.tests.common import EDIBackendTestMixin

from .common import OrderInboundTestMixin


class TestOrderInbound(
    SavepointCase, EDIBackendTestMixin, OrderInboundTestMixin, ComponentMixin
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpComponent()
        cls.backend = cls._get_backend()
        cls._setup_inbound_order(cls.backend)

    def setUp(self):
        super().setUp()
        ComponentMixin.setUp(self)

    @classmethod
    def _get_backend(cls):
        return cls.env.ref("edi_ubl_oca.edi_backend_ubl_demo")

    def test_existing_order_break_on_error(self):
        self.assertEqual(self.exc_record_in.edi_exchange_state, "input_received")
        self.env["sale.order"].create(
            {
                "partner_id": self.order_data.partner.id,
                "client_order_ref": self.order_data.client_order_ref,
            }
        )
        with self.assertRaisesRegex(
            exceptions.UserError, self.err_msg_already_imported
        ):
            self.exc_record_in.with_context(
                _edi_process_break_on_error=True
            ).action_exchange_process()
        self.assertEqual(self.exc_record_in.edi_exchange_state, "input_received")

    def test_existing_order(self):
        self.assertEqual(self.exc_record_in.edi_exchange_state, "input_received")
        self.env["sale.order"].create(
            {
                "partner_id": self.order_data.partner.id,
                "client_order_ref": self.order_data.client_order_ref,
            }
        )
        # Test w/ error handling
        self.exc_record_in.action_exchange_process()
        self.assertEqual(self.exc_record_in.edi_exchange_state, "input_processed_error")
        err_msg = "Sales order has already been imported before"
        self.assertIn(err_msg, self.exc_record_in.exchange_error)

    def test_new_order(self):
        self.assertEqual(self.exc_record_in.edi_exchange_state, "input_received")
        order = self._find_order()
        self.assertFalse(order)
        # Test w/ error handling
        # .with_context(_edi_process_break_on_error=True)
        self.exc_record_in.action_exchange_process()
        self.assertEqual(self.exc_record_in.edi_exchange_state, "input_processed")
        order = self._find_order()
        self.assertEqual(self.exc_record_in.record, order)
        order_msg = order.message_ids[0]
        self.assertIn("Exchange processed successfully", order_msg.body)
        self.assertIn(self.exc_record_in.identifier, order_msg.body)
        self.assertIn(
            f"/web#id={self.exc_record_in.id}&amp;model=edi.exchange.record&amp;view_type=form",
            order_msg.body,
        )
        # TODO: test order data. To do so, first add such tests to sale_order_import
        self.assertEqual(order.order_line.mapped("edi_id"), ["1", "2"])
        self.assertTrue(order.edi_state_id.code, order.EDI_STATE_ORDER_ACCEPTED)
        self.assertTrue(
            order.mapped("order_line.edi_state_id.code"),
            order.EDI_STATE_ORDER_LINE_ACCEPTED,
        )

    def test_cancel(self):
        self.assertEqual(self.exc_record_in.edi_exchange_state, "input_received")
        order = self.env["sale.order"].create(
            {
                "partner_id": self.order_data.partner.id,
                "client_order_ref": self.order_data.client_order_ref,
                "origin_exchange_record_id": self.exc_record_in.id,
            }
        )
        self.exc_record_in._set_related_record(order)
        order.action_confirm()
        self.assertTrue(order.edi_state_id.code, order.EDI_STATE_ORDER_ACCEPTED)
        order.action_cancel()
        self.assertTrue(order.edi_state_id.code, order.EDI_STATE_ORDER_REJECTED)

    def _find_order(self):
        return self.env["sale.order"].search(
            [
                ("client_order_ref", "=", self.order_data.client_order_ref),
                ("commercial_partner_id", "=", self.order_data.partner.parent_id.id),
            ]
        )
