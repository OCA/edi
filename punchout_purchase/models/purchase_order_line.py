# Copyright 2026 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrderLine(models.Model):
    """Track which punchout session a PO line came from.

    When a user clicks "Browse supplier catalog" on a draft PO and walks
    a cart, the returning lines are appended to that PO. This field
    records which session was responsible — useful for debugging,
    auditing, and surfacing on the form a clear distinction between
    lines added manually (no session) and lines pulled in via punchout.

    See ``readme/ROADMAP.md`` for the wider limitation that motivated
    this: TVH's OCI 4.0 SELECT cannot pre-fill the supplier's cart with
    existing PO lines, so a PO with mixed manual+punchout lines is only
    partially visible to the supplier.
    """

    _inherit = "purchase.order.line"

    punchout_session_id = fields.Many2one(
        comodel_name="punchout.session",
        string="Punchout Session",
        readonly=True,
        copy=False,
        index=True,
        help=(
            "If set, this line was added to the PO by the named punchout "
            "session. Lines without a session were added manually and "
            "won't be reflected in the supplier's cart on the next "
            "punchout (OCI SELECT is one-way; the supplier never sees "
            "what's already on the buyer's PO)."
        ),
    )

    def action_open_punchout_catalog(self):
        """Line-level proxy so the Browse-Supplier-Catalog button placed
        inside the order_line ``<control>`` block (next to the standard
        Catalog button) can route to the parent PO's action. Pattern
        mirrors the standard ``action_add_from_catalog`` plumbing."""
        order = self.env["purchase.order"].browse(self.env.context.get("order_id"))
        return order.action_open_punchout_catalog()
