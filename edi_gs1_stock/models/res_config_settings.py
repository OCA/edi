# Copyright 2022 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    gs1_main_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        help="Main UoM for GS1 files",
        related="company_id.gs1_main_uom_id",
        readonly=False,
    )
    gs1_second_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        help="Second UoM for GS1 files",
        related="company_id.gs1_second_uom_id",
        readonly=False,
    )
