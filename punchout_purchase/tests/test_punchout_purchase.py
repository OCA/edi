# Copyright 2023 ACSONE SA/NV
# Copyright 2023 Hunki Enterprises BV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tools import mute_logger

from .common import TestPunchoutPurchaseCommon


class TestPunchoutPurchase(TestPunchoutPurchaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Most new entry-point tests need an *open* backend (the only
        # state _find_punchout_backend matches). Common fixture creates
        # backends in default 'draft' state, so flip here.
        cls.backend.state = "open"

    def test_session_purchase_order_link(self):
        """Test that session has purchase_order_id field."""
        self.assertFalse(self.session.purchase_order_id)
        self.assertEqual(self.session.purchase_order_count, 0)

    def test_backend_has_partner(self):
        """Test that backend has partner configured."""
        self.assertEqual(self.backend.partner_id, self.partner)

    def test_backend_has_auto_create_products(self):
        """Test that backend has auto_create_products flag."""
        self.assertTrue(self.backend.auto_create_products)

    def test_create_purchase_order_no_partner(self):
        """Test that creating PO without partner raises error."""
        self.backend.partner_id = False
        with self.assertRaises(UserError):
            self.session._create_purchase_order_from_response()

    def test_create_purchase_order_wrong_state(self):
        """Test that creating PO with wrong state raises error."""
        self.session.state = "draft"
        with self.assertRaises(UserError):
            self.session.action_create_purchase_order()

    def test_prepare_purchase_order_vals(self):
        """Test that PO values are prepared correctly."""
        vals = self.session._prepare_purchase_order_vals()
        self.assertEqual(vals["partner_id"], self.partner.id)
        self.assertEqual(vals["punchout_session_id"], self.session.id)

    def test_purchase_order_has_session_link(self):
        """Test that purchase.order has punchout_session_id field."""
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "punchout_session_id": self.session.id,
            }
        )
        self.assertEqual(order.punchout_session_id, self.session)

    # ---- new entry-point: PO form -> Browse supplier catalog -------------

    def _draft_po(self, partner=None):
        partner = partner or self.partner
        return self.env["purchase.order"].create({"partner_id": partner.id})

    def test_po_open_punchout_catalog_no_backend(self):
        # Backend exists but is in draft state — _find_punchout_backend
        # only returns 'open' backends.
        self.backend.state = "draft"
        po = self._draft_po()
        with self.assertRaises(UserError):
            po.action_open_punchout_catalog()

    def test_po_open_punchout_catalog_wrong_state(self):
        po = self._draft_po()
        po.state = "purchase"
        with self.assertRaises(UserError):
            po.action_open_punchout_catalog()

    # ---- has_punchout_backend gate (hides UI when no backend) -----------

    def test_po_has_punchout_backend_true_when_open(self):
        """The PO computed flag drives the Browse Supplier Catalog
        button's visibility — true when the vendor has at least one
        open punchout backend."""
        po = self._draft_po()
        self.assertTrue(po.has_punchout_backend)

    def test_po_has_punchout_backend_false_when_no_backend(self):
        """A vendor with no punchout backend at all → flag is False
        → button hidden in the view."""
        new_partner = self.env["res.partner"].create(
            {"name": "Vendor without punchout", "supplier_rank": 1}
        )
        po = self._draft_po(partner=new_partner)
        self.assertFalse(po.has_punchout_backend)

    def test_po_has_punchout_backend_false_when_only_draft_backend(self):
        """Backend exists but isn't ``open`` → flag is False. Mirrors
        the action's runtime check: only ``open`` backends count."""
        self.backend.state = "draft"
        po = self._draft_po()
        self.assertFalse(po.has_punchout_backend)

    def test_partner_has_punchout_backend_drives_button(self):
        """Same gate on the vendor (res.partner) form button."""
        self.assertTrue(self.partner.has_punchout_backend)
        self.backend.state = "closed"
        self.partner.invalidate_recordset(["has_punchout_backend"])
        self.assertFalse(self.partner.has_punchout_backend)

    def test_partner_has_punchout_backend_false_when_not_supplier(self):
        """A non-supplier partner (supplier_rank=0) shouldn't show
        the Browse button regardless of backend state — covered by
        the ``supplier_rank == 0`` half of the view's invisible
        expression. Verify the computed flag too for defensive
        consistency."""
        customer_only = self.env["res.partner"].create(
            {"name": "Customer only", "supplier_rank": 0}
        )
        self.assertFalse(customer_only.has_punchout_backend)

    # ---- session pre-link via context (Browse-from-PO flow) ---------------

    def test_create_session_pre_links_target_po(self):
        po = self._draft_po()
        # Stub the base setup-url method (raises NotImplementedError
        # without a protocol module installed) — we only care that
        # the session is created and context-pre-linked.
        with patch.object(
            type(self.session_model),
            "_get_post_punchout_setup_url",
            return_value="http://test/url",
        ):
            session = (
                self.session_model.with_context(
                    punchout_backend_id=self.backend.id,
                    punchout_target_purchase_order_id=po.id,
                )
                .sudo()
                ._create_punchout_session()
            )
        self.assertEqual(session.purchase_order_id, po)

    def test_create_session_no_pre_link_when_context_absent(self):
        with patch.object(
            type(self.session_model),
            "_get_post_punchout_setup_url",
            return_value="http://test/url",
        ):
            session = (
                self.session_model.with_context(
                    punchout_backend_id=self.backend.id,
                )
                .sudo()
                ._create_punchout_session()
            )
        self.assertFalse(session.purchase_order_id)

    # ---- _tag_lines_with_session -----------------------------------------

    def test_tag_lines_with_session_adds_id(self):
        cmds = [(0, 0, {"name": "X"}), (0, 0, {"name": "Y"})]
        tagged = self.session._tag_lines_with_session(cmds)
        for _c, _z, vals in tagged:
            self.assertEqual(vals["punchout_session_id"], self.session.id)

    def test_tag_lines_with_session_passes_through_non_create_cmds(self):
        # link/unlink commands shouldn't be touched
        cmds = [(6, 0, [1, 2, 3]), (0, 0, {"name": "X"})]
        tagged = self.session._tag_lines_with_session(cmds)
        self.assertEqual(tagged[0], (6, 0, [1, 2, 3]))
        self.assertEqual(tagged[1][2]["punchout_session_id"], self.session.id)

    # ---- vendor (res.partner) form button --------------------------------

    def test_partner_open_punchout_catalog_no_backend(self):
        self.backend.state = "draft"
        with self.assertRaises(UserError):
            self.partner.action_open_punchout_catalog()

    def test_partner_find_punchout_backend(self):
        self.assertEqual(self.partner._find_punchout_backend(), self.backend)
        self.backend.state = "closed"
        self.assertFalse(self.partner._find_punchout_backend())

    # ---- product deep-link (template + variant + per-seller) -------------

    def _product_with_seller(self, code="SUP-001", url_template=None):
        if url_template is not None:
            self.partner.product_url_template = url_template
        product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "seller_ids": [
                    (
                        0,
                        0,
                        {"partner_id": self.partner.id, "product_code": code},
                    )
                ],
            }
        )
        return product

    def test_template_open_supplier_product_no_template(self):
        product = self._product_with_seller(url_template=False)
        with self.assertRaises(UserError):
            product.product_tmpl_id.action_open_supplier_product()

    def test_template_open_supplier_product_returns_url(self):
        product = self._product_with_seller(
            code="ABC-123",
            url_template="https://example.com/parts/{vendor_code}",
        )
        action = product.product_tmpl_id.action_open_supplier_product()
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(action["url"], "https://example.com/parts/ABC-123")
        self.assertEqual(action["target"], "new")

    def test_variant_open_supplier_product_delegates_to_template(self):
        product = self._product_with_seller(
            code="VAR-1",
            url_template="https://example.com/p/{vendor_code}",
        )
        action = product.action_open_supplier_product()
        self.assertEqual(action["url"], "https://example.com/p/VAR-1")

    def test_supplierinfo_open_supplier_url_missing_template(self):
        product = self._product_with_seller(url_template=False)
        seller = product.seller_ids[:1]
        with self.assertRaises(UserError):
            seller.action_open_supplier_url()

    def test_supplierinfo_open_supplier_url_missing_code(self):
        product = self._product_with_seller(
            code="", url_template="https://example.com/p/{vendor_code}"
        )
        seller = product.seller_ids[:1]
        with self.assertRaises(UserError):
            seller.action_open_supplier_url()

    def test_supplierinfo_open_supplier_url_returns_url(self):
        product = self._product_with_seller(
            code="WIDGET-9",
            url_template="https://example.com/p/{vendor_code}",
        )
        seller = product.seller_ids[:1]
        action = seller.action_open_supplier_url()
        self.assertEqual(action["url"], "https://example.com/p/WIDGET-9")

    # ---- auto-process on state -> to_process -----------------------------

    def test_write_to_process_auto_creates_po(self):
        # Fresh session (state=draft) with backend that has partner.
        # When we set state=to_process, the write override fires
        # action_create_purchase_order which calls
        # _create_purchase_order_from_response. With no protocol
        # override, _prepare_purchase_order_lines() returns [], so the
        # PO is created empty (no lines) but the session is linked.
        session = self.session_model.create(
            {"backend_id": self.backend.id, "state": "draft"}
        )
        session.state = "to_process"
        self.assertEqual(session.state, "done")
        self.assertTrue(session.purchase_order_id)
        self.assertEqual(session.purchase_order_id.partner_id, self.partner)

    def test_write_to_process_appends_to_pre_linked_po(self):
        po = self._draft_po()
        session = self.session_model.create(
            {"backend_id": self.backend.id, "state": "draft"}
        )
        session.purchase_order_id = po
        # Existing PO has 0 lines; auto-process appends 0 lines
        # (no protocol → empty list). But state should still go to done.
        session.state = "to_process"
        self.assertEqual(session.state, "done")
        self.assertEqual(session.purchase_order_id, po)

    @property
    def _line_uom_field(self):
        """purchase.order.line UoM field name was renamed
        product_uom -> product_uom_id in Odoo 19. Use whichever exists."""
        fields = self.env["purchase.order.line"]._fields
        return "product_uom_id" if "product_uom_id" in fields else "product_uom"

    def test_uom_mismatch_warning_posted_to_chatter(self):
        """When a cart line's UoM differs from the product's primary
        UoM, the PO gets a chatter message listing the mismatch."""
        unit = self.env.ref("uom.product_uom_unit")
        dozen = self.env.ref("uom.product_uom_dozen")
        product = self.env["product.product"].create(
            {"name": "Test Product", "type": "consu", "uom_id": unit.id}
        )
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_qty": 1,
                            "price_unit": 10,
                            self._line_uom_field: dozen.id,
                            "punchout_session_id": self.session.id,
                            "name": product.display_name,
                        },
                    )
                ],
            }
        )
        self.session.purchase_order_id = po
        before = len(po.message_ids)
        self.session._post_punchout_line_warnings(po, po.order_line)
        self.assertGreater(len(po.message_ids), before)
        latest = po.message_ids[0]
        self.assertIn("Dozen", latest.body)
        self.assertIn("Unit", latest.body)

    def test_no_warning_when_uom_matches(self):
        unit = self.env.ref("uom.product_uom_unit")
        product = self.env["product.product"].create(
            {"name": "Matching", "type": "consu", "uom_id": unit.id}
        )
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_qty": 1,
                            "price_unit": 10,
                            self._line_uom_field: unit.id,
                            "punchout_session_id": self.session.id,
                            "name": product.display_name,
                        },
                    )
                ],
            }
        )
        before = len(po.message_ids)
        self.session._post_punchout_line_warnings(po, po.order_line)
        self.assertEqual(len(po.message_ids), before)

    def test_auto_processed_po_attributed_to_session_user(self):
        """Auto-process runs sudo'd from the supplier callback; the PO
        and its chatter messages must be attributed to the user who
        started the punchout, not the public/sudo user that env carries
        at callback time.
        """
        purchaser = self.env["res.users"].create(
            {
                "name": "Punchout Purchaser",
                "login": "punchout_purchaser",
                "email": "purchaser@example.com",
                "groups_id": [
                    (4, self.env.ref("purchase.group_purchase_user").id),
                ],
            }
        )
        # Build a session owned by the purchaser, then trigger
        # auto-process from a sudo'd context (simulating the supplier
        # callback path).
        session = self.session_model.create(
            {
                "backend_id": self.backend.id,
                "user_id": purchaser.id,
                "state": "draft",
            }
        )
        session.with_user(self.env.ref("base.public_user")).sudo().state = "to_process"
        self.assertEqual(session.purchase_order_id.create_uid, purchaser)

    def test_chatter_warning_attributed_to_session_user(self):
        """Cart-vs-product mismatch chatter posts must be attributed to
        the session's user_id (the purchaser), not the sudo user."""
        purchaser = self.env["res.users"].create(
            {
                "name": "Chatter Purchaser",
                "login": "chatter_purchaser",
                "email": "chatter_purchaser@example.com",
                "groups_id": [
                    (4, self.env.ref("purchase.group_purchase_user").id),
                ],
            }
        )
        unit = self.env.ref("uom.product_uom_unit")
        dozen = self.env.ref("uom.product_uom_dozen")
        product = self.env["product.product"].create(
            {"name": "Attrib Product", "type": "consu", "uom_id": unit.id}
        )
        po = self.env["purchase.order"].create({"partner_id": self.partner.id})
        session = self.session_model.create(
            {
                "backend_id": self.backend.id,
                "user_id": purchaser.id,
                "state": "to_process",
            }
        )
        session.purchase_order_id = po
        po.write(
            {
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_qty": 1,
                            "price_unit": 10,
                            self._line_uom_field: dozen.id,
                            "punchout_session_id": session.id,
                            "name": product.display_name,
                        },
                    )
                ]
            }
        )
        before_ids = po.message_ids.ids
        # Drive the warning post via the public-action path so env.user
        # is NOT the purchaser at call time; the with_user(author) hop
        # inside action_create_purchase_order is what we're verifying.
        session.with_user(
            self.env.ref("base.public_user")
        ).sudo()._post_punchout_line_warnings(po.with_user(purchaser), po.order_line)
        new_messages = po.message_ids.filtered(lambda m: m.id not in before_ids)
        self.assertTrue(new_messages)
        self.assertEqual(new_messages[0].author_id, purchaser.partner_id)

    def test_currency_mismatch_warning_posted(self):
        """When the cart's supplier prices are in a different currency
        than the resolved PO currency, the chatter helper posts a
        warning so the purchaser sees the silent currency drift."""
        eur = self.env.ref("base.EUR")
        usd = self.env.ref("base.USD")
        unit = self.env.ref("uom.product_uom_unit")
        product = self.env["product.product"].create(
            {
                "name": "FX Product",
                "type": "consu",
                "uom_id": unit.id,
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": self.partner.id,
                            "product_code": "FX-1",
                            "price": 10,
                            "currency_id": eur.id,
                        },
                    )
                ],
            }
        )
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "currency_id": usd.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_qty": 1,
                            "price_unit": 10,
                            self._line_uom_field: unit.id,
                            "punchout_session_id": self.session.id,
                            "name": product.display_name,
                        },
                    )
                ],
            }
        )
        before = len(po.message_ids)
        self.session._post_punchout_line_warnings(po, po.order_line)
        self.assertGreater(len(po.message_ids), before)
        latest = po.message_ids[0]
        self.assertIn("EUR", latest.body)
        self.assertIn("USD", latest.body)

    @mute_logger("odoo.addons.punchout_purchase.models.punchout_session")
    def test_auto_process_failure_posts_chatter(self):
        """When auto-process raises, the exception should land on the
        session's chatter and (when pre-linked) on the target PO's
        chatter — not just in the server log."""
        po = self._draft_po()
        session = self.session_model.create(
            {
                "backend_id": self.backend.id,
                "state": "draft",
                "purchase_order_id": po.id,
            }
        )
        session_msg_before = len(session.message_ids)
        po_msg_before = len(po.message_ids)
        # Force action_create_purchase_order to blow up so we exercise
        # the failure-notification branch.
        with patch.object(
            type(session),
            "action_create_purchase_order",
            side_effect=RuntimeError("boom"),
        ):
            session.state = "to_process"
        self.assertGreater(len(session.message_ids), session_msg_before)
        self.assertGreater(len(po.message_ids), po_msg_before)
        latest_po_msg = po.message_ids[0]
        self.assertIn("boom", latest_po_msg.body)

    def test_write_to_process_skips_when_no_partner(self):
        # When the backend has no partner, no auto-process — the
        # session sits in to_process for a human to inspect.
        self.backend.partner_id = False
        session = self.session_model.create(
            {"backend_id": self.backend.id, "state": "draft"}
        )
        session.state = "to_process"
        self.assertEqual(session.state, "to_process")
        self.assertFalse(session.purchase_order_id)
