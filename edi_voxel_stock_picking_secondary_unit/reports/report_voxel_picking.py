# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ReportVoxelPicking(models.AbstractModel):
    _inherit = "report.edi_voxel_stock_picking.template_voxel_picking"

    def _get_product_data(self, line):
        res = super()._get_product_data(line)
        if line.secondary_uom_id and line.secondary_uom_id.voxel_code:
            res.update(
                Qty=str(line.secondary_uom_qty), MU=line.secondary_uom_id.voxel_code,
            )
        return res
