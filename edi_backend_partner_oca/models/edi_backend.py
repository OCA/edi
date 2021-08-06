# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class EdiBackend(models.Model):
    _inherit = "edi.backend"

    partner_id = fields.Many2one(comodel_name="res.partner")
