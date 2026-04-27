## 18.0.1.0.0 (2026)

- [MIG] Migration to Odoo 18.0.
- [FIX] Surface `partner_id`, `company_id`, `product_category_id` and
  `auto_create_products` on the backend form view (the model carried
  these fields but the form never showed them).
- [IMP] Punchout smart button on PO now counts every distinct session
  that contributed lines (not just the originating one) and opens a
  list view when more than one is involved.
- [FIX] PO and chatter messages produced by the supplier-callback
  auto-process are attributed to the session's `user_id` (the
  purchaser who initiated the punchout) instead of the sudo user.
- [FIX] Hide the Punchout smart button and PO-line "Punchout Session"
  column for users without `base.group_system`, so non-admins don't
  see a button that throws an access error on click.
- [IMP] When auto-process fails, post the exception as a chatter
  message on the session (and on the pre-linked PO when set), so
  the purchaser is notified next to the affected record instead of
  having to read server logs.
- [ADD] `USAGE.md` documenting all the new entry points (Browse
  Supplier Catalog, Open at supplier, auto-process, UoM warnings).
- [IMP] Currency-mismatch chatter warning on the PO when the cart's
  supplier prices are in a different currency than the PO's
  pricelist resolved to. Odoo stores raw cart numbers as
  `price_unit`, so a silent currency drift is invisible without
  this hint.
- [FIX] Hide the "Browse supplier catalog" buttons (PO header, PO
  line area, and vendor form smart button) when the vendor has no
  open punchout backend. Previously the button appeared on every
  draft PO; clicking on a non-punchout vendor raised a UserError —
  now the affordance only shows when it's actionable.
