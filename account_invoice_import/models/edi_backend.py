# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EdiBackend(models.Model):
    _inherit = "edi.backend"

    account_invoice_import_config_ids = fields.One2many(
        "account.invoice.import.config", readonly=True, inverse_name="backend_id"
    )
