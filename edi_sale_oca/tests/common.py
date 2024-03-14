# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields


class OrderMixin(object):
    @classmethod
    def _create_sale_order(cls, **kw):
        """Create a sale order

        :return: sale order
        """
        model = cls.env["sale.order"]
        vals = dict(commitment_date=fields.Date.today())
        vals.update(kw)
        so_vals = model.play_onchanges(vals, [])
        if "order_line" in so_vals:
            so_vals["order_line"] = [(0, 0, x) for x in vals["order_line"]]
        return model.create(so_vals)

    @classmethod
    def _setup_order(cls, **kw):
        cls.product_a = cls.env.ref("product.product_product_4")
        cls.product_a.barcode = "1" * 14
        cls.product_b = cls.env.ref("product.product_product_4b")
        cls.product_b.barcode = "2" * 14
        cls.product_c = cls.env.ref("product.product_product_4c")
        cls.product_c.barcode = "3" * 14
        cls.product_d = cls.env.ref("product.product_product_5")
        cls.product_d.barcode = "4" * 14
        line_defaults = kw.pop("line_defaults", {})
        vals = {
            "partner_id": cls.env.ref("base.res_partner_10").id,
            "commitment_date": "2022-07-29",
        }
        vals.update(kw)
        if "client_order_ref" not in vals:
            vals["client_order_ref"] = "ABC123"
        vals["order_line"] = [
            {"product_id": cls.product_a.id, "product_uom_qty": 300, "edi_id": 1000},
            {"product_id": cls.product_b.id, "product_uom_qty": 200, "edi_id": 2000},
            {"product_id": cls.product_c.id, "product_uom_qty": 100, "edi_id": 3000},
        ]
        if line_defaults:
            for line in vals["order_line"]:
                line.update(line_defaults)
        cls.sale = cls._create_sale_order(**vals)
        cls.sale.action_confirm()
