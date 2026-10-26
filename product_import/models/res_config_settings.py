# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    product_import_set_company = fields.Boolean(
        related="company_id.product_import_set_company", readonly=False
    )
