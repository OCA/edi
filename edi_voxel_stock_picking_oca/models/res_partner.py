from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    voxel_picking_report_id = fields.Many2one(
        comodel_name="ir.actions.report",
        domain=[("report_type", "=", "qweb-xml"), ("model", "=", "stock.picking")],
    )

    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + ["voxel_picking_report_id"]
