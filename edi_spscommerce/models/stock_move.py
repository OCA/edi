# Copyright 2026 Daniel Reis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["stock.move"]

    def _edi_sps_uom_code(self):
        """X12 355 code for the move's UoM, or its name when unmapped."""
        self.ensure_one()
        return (
            self.env["edi.sps.uom.map"]._edi_sps_uom_code(self.product_uom)
            or self.product_uom.name
        )
