# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    include_ubl_attachment_in_invoice_email = fields.Boolean(
        related="company_id.include_ubl_attachment_in_invoice_email", readonly=False
    )
