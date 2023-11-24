# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EDIBackend(models.Model):
    _inherit = "edi.backend"

    # TODO: find another way to configure this w/out polluting edi backend
    lsp_partner_id = fields.Many2one(
        string="Logistic Services Provider (LSP)",
        comodel_name="res.partner",
        domain=[("is_lsp", "=", True)],
    )
    lsc_partner_id = fields.Many2one(
        string="Logistic Services Client (LSC)",
        comodel_name="res.partner",
        default=lambda self: self.env.ref("base.main_partner").id,
    )
