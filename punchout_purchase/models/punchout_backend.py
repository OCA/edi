# Copyright 2023 ACSONE SA/NV
# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PunchoutBackend(models.Model):
    _inherit = "punchout.backend"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        help="Default supplier for purchase orders created from this backend.",
    )
    product_category_id = fields.Many2one(
        comodel_name="product.category",
        string="Product Category",
        help="When creating new products, use this category instead of the default.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
    )
    auto_create_products = fields.Boolean(
        default=True,
        help="Automatically create products from cart items if not found.",
    )

    def _get_company(self):
        """Return the company for this backend."""
        self.ensure_one()
        return self.company_id or self.env.company
