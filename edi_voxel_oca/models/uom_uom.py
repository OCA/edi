# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class UoM(models.Model):
    _inherit = "uom.uom"

    voxel_code = fields.Selection(
        selection=[
            ("Unidades", "Unidades"),
            ("Kgs", "Kgs"),
            ("Lts", "Lts"),
            ("Lbs", "Lbs"),
            ("Cajas", "Cajas"),
            ("Bultos", "Bultos"),
            ("Palets", "Palets"),
            ("Horas", "Horas"),
            ("Metros", "Metros"),
            ("MetrosCuadrados", "MetrosCuadrados"),
            ("Contenedores", "Contenedores"),
            ("Otros", "Otros"),
        ],
    )
