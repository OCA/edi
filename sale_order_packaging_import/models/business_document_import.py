# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class BusinessDocumentImport(models.AbstractModel):
    _inherit = "business.document.import"

    def _prepare_order_line_update_values(
        self, existing_line, iline, qty_precision, price_precision
    ):
        values = super()._prepare_order_line_update_values(
            existing_line, iline, qty_precision, price_precision
        )
        product = existing_line.get("product")
        packaging = None
        packaging_code = iline["product"].get("barcode")
        oline = existing_line.get("line")
        if packaging_code:
            packaging = product.packaging_ids.filtered(
                lambda pack: pack.barcode == packaging_code
            )
            if packaging:
                qty = packaging.qty * iline["qty"]
                if qty != oline.product_uom_qty:
                    values["qty"] = [oline.product_uom_qty, qty]
                elif "qty" in values.keys():
                    values.pop("qty")
        if packaging and packaging != oline.product_packaging:
            values["packaging"] = [oline.product_packaging.id, packaging.id]
        elif not packaging and oline.product_packaging:
            values["packaging"] = [oline.product_packaging.id, False]
        return values
