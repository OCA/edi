# Copyright 2023 ACSONE SA/NV
# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    punchout_session_id = fields.Many2one(
        comodel_name="punchout.session",
        string="Punchout Session",
        readonly=True,
        copy=False,
        help=(
            "The session that *originally* created this PO (or appended "
            "the first cart, when the PO existed beforehand). For all "
            "sessions that contributed lines, see "
            "``punchout_session_ids`` — derived from the line tags."
        ),
    )
    punchout_session_ids = fields.Many2many(
        comodel_name="punchout.session",
        compute="_compute_punchout_session_ids",
        string="Punchout Sessions",
        help=(
            "All distinct punchout sessions that contributed lines to "
            "this PO — derived from order_line.punchout_session_id. "
            "Used by the Punchout smart button so it can show a list "
            "view when the PO was built from multiple punchout sessions."
        ),
    )
    punchout_session_count = fields.Integer(
        compute="_compute_punchout_session_ids",
    )

    @api.depends("order_line.punchout_session_id", "punchout_session_id")
    def _compute_punchout_session_ids(self):
        for rec in self:
            sessions = rec.order_line.mapped("punchout_session_id")
            # Include the originating session even if all its lines were
            # later deleted, so the smart button never goes blank for a
            # PO that was demonstrably born from a punchout.
            if rec.punchout_session_id:
                sessions |= rec.punchout_session_id
            rec.punchout_session_ids = sessions
            rec.punchout_session_count = len(sessions)

    def action_view_punchout_session(self):
        """Open the related punchout session(s).

        Single session → open the form view directly.
        Multiple sessions → open a filtered list so the user can drill
        into each one (matches default Odoo smart-button behaviour for
        one2many-shaped relations).
        """
        self.ensure_one()
        sessions = self.punchout_session_ids
        if len(sessions) <= 1:
            return {
                "type": "ir.actions.act_window",
                "res_model": "punchout.session",
                "view_mode": "form",
                "res_id": (sessions or self.punchout_session_id).id,
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Punchout Sessions"),
            "res_model": "punchout.session",
            "view_mode": "list,form",
            "domain": [("id", "in", sessions.ids)],
        }

    def action_open_punchout_catalog(self):
        """Browse the supplier's catalog and append the cart's lines to
        this draft PO when the supplier returns it.

        The session is pre-linked to ``self.id`` via context so that
        ``punchout.session.action_create_purchase_order`` appends to
        this PO instead of creating a new one.

        IMPORTANT (limitation for OCI 4.0 SELECT): existing lines on this
        PO are *not* sent to the supplier. The user only sees the
        supplier's empty cart on the supplier site; lines they've
        already added manually in Odoo stay in Odoo and won't be
        reflected on the supplier side until cart-pre-fill is
        implemented (OCI 5+ extended modes / cXML SetupRequest with
        current cart). See ``readme/ROADMAP.md``.
        """
        self.ensure_one()
        if self.state != "draft":
            raise UserError(
                _(
                    "Punchout from PO is only available on draft "
                    "purchase orders (current state: %(state)s)."
                )
                % {"state": self.state}
            )
        if not self.partner_id:
            raise UserError(
                _("Set a vendor on this purchase order before browsing the catalog.")
            )
        backend = self.partner_id._find_punchout_backend()
        if not backend:
            raise UserError(
                _(
                    "No open punchout backend is configured for "
                    "supplier %(name)s. Configure one under PunchOut → "
                    "Backends and set its state to Open."
                )
                % {"name": self.partner_id.display_name}
            )
        return (
            self.env["punchout.session"]
            .with_context(
                punchout_backend_id=backend.id,
                punchout_target_purchase_order_id=self.id,
            )
            ._redirect_to_punchout()
        )
