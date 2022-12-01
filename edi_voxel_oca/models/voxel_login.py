# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class VoxelLogin(models.Model):
    _name = "voxel.login"
    _description = "Voxel login"

    name = fields.Char(required=True)
    url = fields.Char(string="URL", required=True)
    user = fields.Char(required=True)
    password = fields.Char(required=True)
    company_id = fields.Many2one(comodel_name="res.company", string="Company")
