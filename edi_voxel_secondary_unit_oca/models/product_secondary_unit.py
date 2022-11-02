# Copyright 2021 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.edi_voxel_oca.models.uom_uom import VOXEL_CODE


class ProductSecondaryUnit(models.Model):
    _inherit = "product.secondary.unit"

    voxel_code = fields.Selection(selection=VOXEL_CODE)
