# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.fields import Command

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.purchase_order_import.wizard.purchase_order_response_import import (
    LINE_STATUS_ACCEPTED,
)


class TestPurchaseOrderResponseImportCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.supplier = cls.env["res.partner"].create(
            {
                "name": "Order Response Supplier",
                "supplier_rank": 1,
                "vat": "BE0477472701",
            }
        )
        cls.env.company.partner_id.vat = "BE0421801233"
        cls.currency_euro = cls.env.ref("base.EUR")
        cls.currency_usd = cls.env.ref("base.USD")
        (cls.currency_euro + cls.currency_usd).action_unarchive()
        cls.product_uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.product_1 = cls.env["product.product"].create(
            {
                "name": "Product 1",
                "seller_ids": [
                    Command.create(
                        {"partner_id": cls.supplier.id, "product_code": "P1"}
                    )
                ],
            }
        )
        cls.product_2 = cls.env["product.product"].create(
            {
                "name": "Product 2",
                "seller_ids": [
                    Command.create(
                        {"partner_id": cls.supplier.id, "product_code": "P2"}
                    )
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
                "product_uom_id": cls.product_uom_unit.id,
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
                "product_uom_id": cls.product_uom_unit.id,
                "price_unit": 25,
            }
        )
        cls.OrderResponseImport = cls.env["purchase.order.response.import"]

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
            "uom": {"unece_code": order_line.product_uom_id.unece_code},
        }
