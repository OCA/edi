# Copyright 2026 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class ProductSupplierinfo(models.Model):
    """Per-seller deep-link to the supplier's product detail page.

    Putting the action on the supplierinfo (not on product.template)
    means the seller_ids list on a product form gets one button per
    row — no ambiguity about which vendor will open. Especially useful
    for products sourced from multiple suppliers.
    """

    _inherit = "product.supplierinfo"

    def action_open_supplier_url(self):
        self.ensure_one()
        template = self.partner_id.product_url_template
        if not template:
            raise UserError(
                _(
                    "Supplier %(name)s has no Product URL Template "
                    "configured. Set one on the supplier's contact "
                    "form (Sales & Purchase tab)."
                )
                % {"name": self.partner_id.display_name}
            )
        if not self.product_code:
            raise UserError(
                _(
                    "Set a Reference Code on this vendor row before "
                    "opening — the URL template needs the supplier's "
                    "product code to substitute."
                )
            )
        return {
            "type": "ir.actions.act_url",
            "url": template.replace("{vendor_code}", self.product_code),
            "target": "new",
        }
