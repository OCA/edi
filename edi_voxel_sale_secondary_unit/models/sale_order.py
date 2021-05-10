# Copyright 2021 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _parse_qty_uom_voxel(self, line_vals, line_element):
        """ Override to use secondary unit instead standard UoM """
        product_data = line_element.attrib
        product_id = line_vals.get("product_id")
        product = self.env["product.product"].browse(product_id)
        qty = float(product_data.get("Qty", "1"))
        mu = product_data.get("MU")
        secondary_uom = product.secondary_uom_ids.filtered(lambda r: r.voxel_code == mu)
        if secondary_uom:
            line_vals.update(
                secondary_uom_qty=qty, secondary_uom_id=secondary_uom[0].id
            )
        else:
            super()._parse_qty_uom_voxel(line_vals, line_element)
