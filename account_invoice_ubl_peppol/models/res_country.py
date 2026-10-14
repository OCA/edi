# Copyright 2021 Sunflower IT (<https://sunflowerweb.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCountry(models.Model):
    _inherit = "res.country"

    peppol_eas_code = fields.Many2one("peppol.eas.list", "EAS code")
