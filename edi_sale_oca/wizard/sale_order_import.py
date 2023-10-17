# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


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
        # TODO: we should probably add an ext reference field to s.o.l. in sale_order_import
        # and get rid of this override.
        vals["edi_id"] = import_line.get("order_line_ref") or import_line.get(
            "sequence"
        )
        return vals
