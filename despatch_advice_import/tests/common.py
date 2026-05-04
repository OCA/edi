# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestDespatchAdviceImportCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.DespatchAdviceImport = cls.env["despatch.advice.import"]
        cls.env.company.partner_id.vat = "BE0421801233"
        cls.supplier = cls.env["res.partner"].create(
            {
                "name": "Test Supplier",
                "supplier_rank": 1,
                "vat": "BE0477472701",
            }
        )

    @classmethod
    def _create_product(cls, name, code, supplier_code):
        return cls.env["product.product"].create(
            {
                "name": name,
                "default_code": code,
                "seller_ids": [
                    Command.create(
                        {
                            "partner_id": cls.supplier.id,
                            "product_code": supplier_code,
                        }
                    )
                ],
            }
        )

    @classmethod
    def _get_po_line_vals(cls, product, product_qty, price_unit):
        return {
            "product_id": product.id,
            "name": product.name,
            "date_planned": fields.Datetime.now(),
            "product_qty": product_qty,
            "product_uom_id": cls.env.ref("uom.product_uom_unit").id,
            "price_unit": price_unit,
        }

    @classmethod
    def _create_purchase_order(cls, line_vals_list):
        return cls.env["purchase.order"].create(
            {
                "partner_id": cls.supplier.id,
                "date_order": fields.Datetime.now(),
                "date_planned": fields.Datetime.now(),
                "order_line": [Command.create(vals) for vals in line_vals_list],
            }
        )
