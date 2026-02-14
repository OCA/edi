# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    invoice_import_facturx_allowance_separate_line = fields.Boolean(
        related="company_id.invoice_import_facturx_allowance_separate_line",
        readonly=False,
    )
