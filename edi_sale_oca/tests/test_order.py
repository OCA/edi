# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from odoo.addons.edi_oca.tests.common import EDIBackendTestMixin

from .common import OrderMixin


class TestOrder(TransactionCase, EDIBackendTestMixin, OrderMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # force metadata storage w/ proper key
        cls.env = cls.env(context=dict(cls.env.context, edi_framework_action=True))
        cls._setup_records()
        cls.exchange_type_in.exchange_filename_pattern = "{record.id}-{type.code}-{dt}"
        cls.exc_record_in = cls.backend.create_record(
            cls.exchange_type_in.code, {"edi_exchange_state": "input_received"}
        )
        cls._setup_order(
            origin_exchange_record_id=cls.exc_record_in.id,
        )

    def test_line_origin(self):
        order = self.sale
        self.assertEqual(order.origin_exchange_record_id, self.exc_record_in)
        lines = order.order_line
        self.env["sale.order.line"].create(
            [
                {
                    "order_id": order.id,
                    "product_id": self.product_d.id,
                    "product_uom_qty": 300,
                    "edi_id": 4000,
                },
                {
                    "order_id": order.id,
                    "product_id": self.product_d.id,
                    "product_uom_qty": 400,
                    "edi_id": 5000,
                },
            ]
        )
        order.env.invalidate_all()
        new_line1, new_line2 = order.order_line - lines
        self.assertEqual(new_line1.origin_exchange_record_id, self.exc_record_in)
        self.assertEqual(new_line2.origin_exchange_record_id, self.exc_record_in)
