# Copyright 2026 Daniel Reis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "edi.exchange.consumer.mixin"]


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ["account.move.line"]

    def _edi_sps_uom_code(self):
        """X12 355 code for the line's UoM, or its name when unmapped."""
        self.ensure_one()
        return (
            self.env["edi.sps.uom.map"]._edi_sps_uom_code(self.product_uom_id)
            or self.product_uom_id.name
        )
