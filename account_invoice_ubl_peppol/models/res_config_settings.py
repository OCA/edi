# Copyright 2021 Sunflower IT (<https://sunflowerweb.nl>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ubl_domain_peppol = fields.Text(
        related="company_id.ubl_domain_peppol", readonly=False
    )
    ubl_default_tax = fields.Many2one(
        comodel_name="account.tax",
        related="company_id.ubl_default_tax",
        readonly=False,
    )
    ubl_default_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        related="company_id.ubl_default_uom_id",
        readonly=False,
    )
