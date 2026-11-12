# Copyright 2026 Daniel Reis
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class EdiSpsUomMap(models.Model):
    _name = "edi.sps.uom.map"
    _description = "SPS Commerce UOM code mapping"
    _rec_name = "code"

    code = fields.Char(
        "UOM code",
        required=True,
        index=True,
        help="X12 355 unit-of-measure code sent by SPS in OrderQtyUOM.",
    )
    uom_id = fields.Many2one(
        "uom.uom",
        string="Unit of Measure",
        required=True,
        ondelete="cascade",
    )

    _sql_constraints = [
        ("code_uniq", "unique(code)", "Each UOM code can only be mapped once."),
    ]

    @api.model
    def _edi_sps_uom_code(self, uom):
        """Return the X12 355 code for ``uom``, or False when unmapped."""
        if not uom:
            return False
        rec = self.search([("uom_id", "=", uom.id)], limit=1)
        return rec.code or False
