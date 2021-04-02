# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

VOXEL_CODE = [
    ("Unidades", "Units"),
    ("Kgs", "Kgs"),
    ("Lts", "Liters"),
    ("Lbs", "Lbs"),
    ("Cajas", "Boxes"),
    ("Bultos", "Packages"),
    ("Palets", "Pallets"),
    ("Horas", "Hours"),
    ("Metros", "Meters"),
    ("MetrosCuadrados", "Square meters"),
    ("Contenedores", "Containers"),
    ("Otros", "Others"),
]


class UoM(models.Model):
    _inherit = "uom.uom"

    voxel_code = fields.Selection(selection=VOXEL_CODE)
