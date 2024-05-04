# Copyright 2022 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    gs1_main_uom_id = fields.Many2one(
        comodel_name="uom.uom", string="GS1 main UoM", help="Main UoM for GS1 files"
    )

    gs1_second_uom_id = fields.Many2one(
        comodel_name="uom.uom", string="GS1 second UoM", help="Second UoM for GS1 files"
    )
