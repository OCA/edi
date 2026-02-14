# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    invoice_import_facturx_allowance_separate_line = fields.Boolean(
        "FacturX Import Allowance Separate Line",
        default=True,
        help="This allows to create allowances or charges "
        "as separate lines when importing FacturX invoices",
    )
