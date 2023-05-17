# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

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
        if not vals.get("customer_ref"):
            customer_ref = self._get_order_line_customer_ref(import_line)
            if customer_ref:
                vals["customer_ref"] = customer_ref
        return vals

    def _prepare_update_order_line_vals(self, change_dict):
        vals = super()._prepare_update_order_line_vals(change_dict)
        customer_ref = self._get_order_line_customer_ref(vals)
        if customer_ref:
            vals["customer_ref"] = customer_ref
        return vals

    def _get_order_line_customer_ref(self, vals):
        """Extrapolate customer ref notes

        `sale_order_import_ubl` will extract notes from
        `cac:OrderLine/cbc:Note` and `cac:OrderLine/cac:LineItem/cbc:Note`.
        """
        customer_ref = ""
        note = vals.get("note", "").strip()
        if note:
            for line in note.splitlines():
                if "customer_ref:" in line:
                    customer_ref = line.replace("customer_ref:", "").strip()
                    break
        return customer_ref
