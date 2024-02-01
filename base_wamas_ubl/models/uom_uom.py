# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class UomUom(models.Model):
    _inherit = "uom.uom"

    wamas_code = fields.Char(
        string="WAMAS Code",
    )
