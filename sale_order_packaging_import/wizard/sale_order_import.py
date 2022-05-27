# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class SaleOrderImport(models.TransientModel):
    _inherit = "sale.order.import"

    @api.model
    def _prepare_create_order_line(
        self, product, uom, order, import_line, price_source
    ):
        vals = super()._prepare_create_order_line(
            product, uom, order, import_line, price_source
        )
        packaging_code = import_line["product"].get("barcode")
        if packaging_code:
            packaging = product.packaging_ids.filtered(
                lambda pack: pack.barcode == packaging_code
            )
            if packaging:
                vals["product_packaging"] = packaging.id
                vals["product_uom_qty"] = 0
                vals["product_packaging_qty"] = import_line["qty"]
        return vals

    def _prepare_update_order_line_vals(self, change_dict):
        vals = super()._prepare_update_order_line_vals(change_dict)
        if "packaging" in change_dict:
            vals.update({"product_packaging": change_dict["packaging"][1]})
        return vals
