# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_order_ubl_import_http_confirmed = fields.Boolean(
        related="company_id.sale_order_ubl_import_http_confirmed", readonly=False
    )
