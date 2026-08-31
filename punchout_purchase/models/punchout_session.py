# Copyright 2023 ACSONE SA/NV
# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PunchoutSession(models.Model):
    _inherit = "punchout.session"

    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Purchase Order",
        readonly=True,
        help=(
            "When set BEFORE the cart is received (the user started "
            "the punchout from a draft PO), the returning lines are "
            "appended to this PO instead of creating a new one. "
            "When set AFTER the cart is received, this is the PO that "
            "was created from the session."
        ),
    )

    @api.model
    def _create_punchout_session(self):
        """Pre-link the session to a target PO when one was specified
        via context (set by ``purchase.order.action_open_punchout_catalog``).
        Falls back to the base behaviour (no PO pre-link) when not set.
        """
        session = super()._create_punchout_session()
        target_po_id = self.env.context.get("punchout_target_purchase_order_id")
        if target_po_id:
            session.sudo().purchase_order_id = target_po_id
        return session

    purchase_order_count = fields.Integer(
        compute="_compute_purchase_order_count",
    )

    def _compute_purchase_order_count(self):
        for rec in self:
            rec.purchase_order_count = 1 if rec.purchase_order_id else 0

    def action_view_purchase_order(self):
        """Open the related purchase order."""
        self.ensure_one()
        if not self.purchase_order_id:
            raise UserError(_("No purchase order linked to this session."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "view_mode": "form",
            "res_id": self.purchase_order_id.id,
        }

    def action_process(self):
        """When a supplier is configured, "Process" creates the purchase order
        (or appends to a pre-linked PO) instead of just marking the session
        done — the create/append is what the user almost always wants once
        the cart has been received."""
        self.ensure_one()
        if self.state == "to_process" and self.backend_id.partner_id:
            return self.action_create_purchase_order()
        return super().action_process()

    def action_create_purchase_order(self):
        """Create or append a purchase order from the session response.

        If ``purchase_order_id`` is pre-set on the session (the user
        started the punchout from an existing draft PO), the cart's
        lines are appended to that PO. Otherwise a new PO is created.

        All PO writes/creates and chatter posts are performed under
        ``self.user_id`` (the purchaser who initiated the session) so
        the audit trail attributes the work to a real human, not the
        sudo'd context the supplier callback runs in.
        """
        self.ensure_one()
        if self.state != "to_process":
            raise UserError(
                _("Session must be in 'To Process' state to create a purchase order.")
            )
        # The supplier-callback path is ``auth="none"``; ``env.user``
        # there can be the public user OR an empty recordset
        # depending on the Odoo version + how sudo / auth interact.
        # Calling ``with_user(empty)`` is a no-op (returns self
        # unchanged), and the empty-env then poisons the deeper
        # product-create chain (``stock._default_responsible_id``
        # crashes on ``self.env.user._is_superuser()``).
        # Resolution order:
        #   1. session.user_id (the human who clicked the punchout
        #      button — best for audit attribution)
        #   2. env.user (if non-empty)
        #   3. OdooBot / SUPERUSER (system fallback, always exists)
        author = self.user_id or self.env.user
        if not author or not author.id:
            # OdooBot is the right system fallback over a human admin:
            # signals "system action" in the chatter (no confusion
            # with manual admin edits) and runs in superuser mode.
            author = self.env.ref("base.user_root")
        if self.purchase_order_id:
            # Append-to-existing flow (started from a draft PO).
            if self.purchase_order_id.state not in ("draft", "sent"):
                raise UserError(
                    _(
                        "Purchase order %(name)s is no longer editable; "
                        "cannot append lines from a punchout session."
                    )
                    % {"name": self.purchase_order_id.display_name}
                )
            new_line_cmds = self._tag_lines_with_session(
                self._prepare_purchase_order_lines()
            )
            if new_line_cmds:
                self.purchase_order_id.with_user(author).write(
                    {"order_line": new_line_cmds}
                )
            self.write({"state": "done"})
        else:
            order = self.with_user(author)._create_purchase_order_from_response()
            self.write(
                {
                    "purchase_order_id": order.id,
                    "state": "done",
                }
            )
        # Post any cart-vs-product mismatch warnings to the PO chatter
        # so the purchaser sees them before confirming.
        new_lines = self.purchase_order_id.order_line.filtered(
            lambda line: line.punchout_session_id == self
        )
        self._post_punchout_line_warnings(
            self.purchase_order_id.with_user(author), new_lines
        )
        return self.action_view_purchase_order()

    def _build_line_mismatch_messages(self, line):
        """Return a list of human-readable mismatch warnings for one new line.

        Generic across protocols. Today only the UoM check is
        implemented because that one materially changes ordered
        quantity (Box vs Unit). Price and description differences are
        expected (suppliers send their own values) and don't trigger
        noise. Override / extend in subclasses for protocol-specific
        checks (e.g. cart price wildly above existing supplierinfo).
        """
        self.ensure_one()
        warnings = []
        product = line.product_id
        # The UoM field on PO line was renamed product_uom -> product_uom_id
        # in Odoo 19; tolerate both.
        line_uom = getattr(line, "product_uom_id", None) or getattr(
            line, "product_uom", None
        )
        if line_uom and product and product.uom_id and line_uom != product.uom_id:
            warnings.append(
                _(
                    "%(name)s: cart UoM <strong>%(cart)s</strong> differs "
                    "from the product's primary UoM <strong>%(prod)s</strong>. "
                    "Verify the line quantity before confirming — Odoo "
                    "applies any same-category conversion automatically, "
                    "but cross-category or unmapped supplier UoMs may "
                    "have been silently coerced to the product default."
                )
                % {
                    "name": product.display_name,
                    "cart": line_uom.display_name,
                    "prod": product.uom_id.display_name,
                }
            )
        return warnings

    def _build_currency_mismatch_message(self, order, new_lines):
        """Compare the cart's per-supplier price currency against the
        PO's currency. Returns a single warning string when they
        differ, or ``None``.

        We can't recover the cart's currency from the line itself
        (the cart's currency code lives on the auto-created /
        matched ``product.supplierinfo``), so we read it back from
        the seller for this backend's partner. Important because
        Odoo silently stores raw cart prices on the PO line — if
        the cart sent EUR and the PO is USD, every ``price_unit``
        is now an EUR number masquerading as USD."""
        self.ensure_one()
        partner = self.backend_id.partner_id
        if not (partner and order.currency_id):
            return None
        cart_currencies = set()
        for line in new_lines:
            seller = line.product_id.seller_ids.filtered(
                lambda s, p=partner: s.partner_id == p
            )[:1]
            if seller and seller.currency_id:
                cart_currencies.add(seller.currency_id)
        mismatched = {c for c in cart_currencies if c != order.currency_id}
        if not mismatched:
            return None
        return _(
            "PO currency is <strong>%(po)s</strong> but the cart's "
            "supplier prices are in <strong>%(cart)s</strong>. Odoo "
            "stores raw cart numbers as ``price_unit``, so each line's "
            "price is a %(cart)s value being treated as %(po)s. "
            "Verify the lines (and consider switching the PO's pricelist) "
            "before confirming."
        ) % {
            "po": order.currency_id.display_name,
            "cart": ", ".join(c.display_name for c in mismatched),
        }

    def _post_punchout_line_warnings(self, order, new_lines):
        """Post one chatter message on the PO bundling all warnings
        from the cart vs the resolved PO/product data — keeps the
        audit trail compact.

        Two classes of check today:
        * per-line UoM mismatch (cart UoM != product's primary UoM)
        * PO-level currency mismatch (cart prices in a different
          currency than the PO's pricelist resolved to)
        Override / extend in subclasses for protocol-specific checks.
        """
        self.ensure_one()
        if not new_lines:
            return
        all_warnings = []
        for line in new_lines:
            all_warnings.extend(self._build_line_mismatch_messages(line))
        currency_msg = self._build_currency_mismatch_message(order, new_lines)
        if currency_msg:
            all_warnings.append(currency_msg)
        if not all_warnings:
            return
        body = (
            _("Punchout cart vs Odoo product data — discrepancies on this PO:")
            + "<ul><li>"
            + "</li><li>".join(all_warnings)
            + "</li></ul>"
        )
        order.message_post(body=body)

    def _tag_lines_with_session(self, line_cmds):
        """Inject ``punchout_session_id`` into every (0, 0, vals) command.

        Called from action_create_purchase_order — done at that layer
        rather than overriding _prepare_purchase_order_lines because
        protocol modules (cxml/oci/ids) override _prepare_ without
        calling super, so an override-based approach silently no-ops
        for those protocols (the most common ones)."""
        tagged = []
        for cmd in line_cmds:
            if isinstance(cmd, list | tuple) and cmd[0] == 0 and len(cmd) == 3:
                vals = {**cmd[2], "punchout_session_id": self.id}
                tagged.append((0, 0, vals))
            else:
                tagged.append(cmd)
        return tagged

    def _create_purchase_order_from_response(self):
        """Create purchase order from response. Override in protocol modules."""
        self.ensure_one()
        backend = self.backend_id
        if not backend.partner_id:
            raise UserError(
                _("Please configure a supplier on the backend %(name)s.")
                % {"name": backend.display_name}
            )

        order_vals = self._prepare_purchase_order_vals()
        return self.env["purchase.order"].create(order_vals)

    def _prepare_purchase_order_vals(self):
        """Prepare values for purchase order creation."""
        self.ensure_one()
        backend = self.backend_id
        return {
            "partner_id": backend.partner_id.id,
            "company_id": backend._get_company().id,
            "punchout_session_id": self.id,
            "order_line": self._tag_lines_with_session(
                self._prepare_purchase_order_lines()
            ),
        }

    def write(self, vals):
        """Auto-process the cart when state moves to ``to_process``.

        Once the supplier's POST has populated the session and the
        cart is parsed, the user almost never wants the session to sit
        in to_process — they want the PO. Auto-fire
        action_create_purchase_order so the redirect lands the user
        on a PO with the new lines visible. Skips when the backend
        has no supplier configured (manual-review fallback).

        **System-user attribution** for the state-tracking message
        and the auto-process create chain: the supplier-callback
        controller is ``auth="none"``, so ``env.user`` may be empty
        / public. Standard ``mail.thread`` would attribute the
        state-tracking message to "unknown" and the deeper product-
        create chain crashes on
        ``self.env.user._is_superuser()`` (``Expected singleton:
        res.users()``). Switch the env to admin **before** calling
        super so:
          * the tracking message has a real author (admin → renders
            as "Administrator" / "OdooBot" depending on the install)
          * the auto-process flow has ``self.env.user`` = admin,
            avoiding the empty-singleton crash deep in stock's
            ``_default_responsible_id``
        Per-line / per-PO attribution to the punchout-initiating
        user (``session.user_id``) still happens inside
        ``action_create_purchase_order`` via ``with_user(author)``
        for the actual writes — only the system-level entry point
        is admin.

        On failure, surface the error in the session's chatter and
        on the pre-linked PO's chatter so the purchaser is notified
        next to the affected record instead of having to dig through
        server logs."""
        # Detect controller-path writes (env.uid is None / empty) and
        # re-enter under OdooBot's identity. ``not self.env.uid``
        # covers both the literal-None case and the public-user case
        # where the public user can't even read its own res.users
        # record. OdooBot (``base.user_root``, the SUPERUSER) is the
        # right choice over a human admin: it signals "system action"
        # in the chatter (avoids confusion with manual admin edits),
        # and ``with_user(SUPERUSER)`` implicitly enables superuser
        # mode (per Odoo docstring: "by convention, the superuser is
        # always in superuser mode") so the deeper product-create
        # chain bypasses any partner / company ACLs that would
        # otherwise resolve env.user to an empty recordset.
        if (
            vals.get("state") == "to_process"
            and not self.env.context.get("skip_punchout_auto_process")
            and (not self.env.uid or not self.env.user)
        ):
            odoobot = self.env.ref("base.user_root")
            return self.with_user(odoobot).write(vals)
        res = super().write(vals)
        if vals.get("state") == "to_process":
            for rec in self:
                if rec.backend_id.partner_id and not self.env.context.get(
                    "skip_punchout_auto_process"
                ):
                    try:
                        rec.with_context(
                            skip_punchout_auto_process=True
                        ).action_create_purchase_order()
                    except Exception as e:  # noqa: BLE001
                        _logger.warning(
                            "Auto-process of session %s failed; user can "
                            "still click Process manually. Error: %s",
                            rec.display_name,
                            e,
                        )
                        rec._notify_auto_process_failure(e)
        return res

    def _notify_auto_process_failure(self, exc):
        """Post a chatter message on the session and (when pre-linked)
        on the target PO so the purchaser is notified of the failure
        rather than having to discover it from the session staying in
        ``to_process``.

        Defensive: this method is called from the failure branch of
        the auto-process flow, which itself runs from an
        ``auth="none"`` controller. ``env.user`` may be empty or the
        public user. Fall through to OdooBot (SUPERUSER) so the
        chatter post never crashes — losing the notification entirely
        is worse than attributing it to OdooBot.
        """
        self.ensure_one()
        author = self.user_id or self.env.user
        if not author or not author.id:
            author = self.env.ref("base.user_root")
        body = _(
            "Auto-creation of the purchase order failed. The session "
            "remains in <strong>To Process</strong> — open it and "
            "click Process to retry once the issue is resolved.<br/>"
            "Error: <code>%(err)s</code>"
        ) % {"err": exc}
        # Both message_posts wrapped in their own try/except — even the
        # safety-net author resolution can't help if message_post itself
        # raises (e.g. mail module misconfigured). The session stays in
        # to_process and the user can still click Process manually.
        try:
            self.sudo().with_user(author).message_post(body=body)
        except Exception as inner_exc:  # noqa: BLE001
            _logger.warning(
                "Punchout session %s: failed to post auto-process "
                "failure chatter on the session: %s",
                self.display_name,
                inner_exc,
            )
        if self.purchase_order_id:
            try:
                self.purchase_order_id.sudo().with_user(author).message_post(body=body)
            except Exception as inner_exc:  # noqa: BLE001
                _logger.warning(
                    "Punchout session %s: failed to post auto-process "
                    "failure chatter on PO %s: %s",
                    self.display_name,
                    self.purchase_order_id.display_name,
                    inner_exc,
                )

    def _prepare_purchase_order_lines(self):
        """Prepare order lines from response. Override in protocol modules."""
        # This should be overridden by protocol-specific modules
        return []

    def _get_redirect_url(self):
        """Redirect to purchase order after processing."""
        self.ensure_one()
        if self.purchase_order_id:
            order_id = self.purchase_order_id.id
            return f"/web#id={order_id}&model=purchase.order&view_type=form"
        return super()._get_redirect_url()
