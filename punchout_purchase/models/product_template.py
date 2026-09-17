# Copyright 2026 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    """Open this product on a supplier's website (deep-link, not punchout).

    Looks for a ``supplierinfo`` whose partner has a
    ``product_url_template``, substitutes ``{vendor_code}`` with the
    seller's product code, and returns an action redirecting the user.

    No punchout session is created — this is a simple URL deep-link
    intended for sourcing decisions, datasheet / spec lookup, and
    discovering alternatives on the supplier's catalog.
    """

    _inherit = "product.template"

    def action_open_supplier_product(self):
        """Open the first matching supplierinfo's product URL in a new tab."""
        self.ensure_one()
        for seller in self.seller_ids:
            template = seller.partner_id.product_url_template
            code = seller.product_code
            if template and code:
                return {
                    "type": "ir.actions.act_url",
                    "url": template.replace("{vendor_code}", code),
                    "target": "new",
                }
        raise UserError(
            _(
                "No supplier on this product has a URL template + "
                "product code configured. Set a Product URL Template "
                "on the supplier (Contacts form), and a Reference "
                "Code on the product's vendor info."
            )
        )


class ProductProduct(models.Model):
    """Variant-level proxy so the smart button on the variant form
    (which bound to ``product.product``) routes to the template's
    implementation. Without this, clicking the button on a variant
    raises ``AttributeError: The method 'product.product.
    action_open_supplier_product' does not exist``."""

    _inherit = "product.product"

    def action_open_supplier_product(self):
        self.ensure_one()
        return self.product_tmpl_id.action_open_supplier_product()
