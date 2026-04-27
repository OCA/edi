# Copyright 2026 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    product_url_template = fields.Char(
        string="Product URL Template",
        help=(
            "URL template the supplier exposes for individual product "
            "pages. ``{vendor_code}`` is substituted with the value of "
            "``product.supplierinfo.product_code``. Example: "
            "``https://eshop.tvh.com/parts/{vendor_code}``. Used by the "
            "'Open at supplier' button on product forms — the lookup is "
            "purely a deep-link, no punchout session is initiated."
        ),
    )

    def _find_punchout_backend(self):
        """Return the (single) open punchout backend for this partner.

        Returns an empty recordset if none configured. Multiple-backend
        scenarios (e.g. industrial + agricultural at TVH) are out of
        scope for the simple "Browse" buttons; they'd want a wizard,
        which is on the roadmap.
        """
        self.ensure_one()
        return self.env["punchout.backend"].search(
            [
                ("partner_id", "=", self.id),
                ("state", "=", "open"),
            ],
            limit=1,
        )

    def action_open_punchout_catalog(self):
        """Browse this supplier's punchout catalog (no PO context)."""
        self.ensure_one()
        backend = self._find_punchout_backend()
        if not backend:
            raise UserError(
                _(
                    "No open punchout backend is configured for "
                    "supplier %(name)s. Configure one under PunchOut → "
                    "Backends and set its state to Open."
                )
                % {"name": self.display_name}
            )
        return (
            self.env["punchout.session"]
            .with_context(punchout_backend_id=backend.id)
            ._redirect_to_punchout()
        )
