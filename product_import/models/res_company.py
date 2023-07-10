# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    product_import_set_company = fields.Boolean(
        string="Set company on imported product",
        help="If active, then products are company-specific. "
        "Beware that by default `barcode` is unique for all companies. "
        "Install OCA add-on `product_barcode_constraint_per_company` "
        "to circumvent this limitation.",
    )
