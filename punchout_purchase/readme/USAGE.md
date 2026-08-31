This module adds three purchaser-facing entry points on top of the
base `punchout` flow.

## Browse Supplier Catalog from a draft PO

On a draft purchase order whose vendor has at least one **Open**
punchout backend, a **Browse Supplier Catalog** button appears in
the header (and as a link next to the standard *Catalog* link in the
order-line area).

Clicking it opens a punchout session pre-linked to the current PO.
When the supplier returns the cart, the lines are *appended* to the
PO instead of creating a new one.

> ⚠️ **Limitation:** existing manual lines on the PO are **not** sent
> to the supplier. The supplier's site shows an empty cart. This is
> a protocol limitation (cart pre-fill needs OCI 5+ or cXML
> SetupRequest with current-cart payload). See `ROADMAP.md`.

## Browse Supplier Catalog from a vendor record

The vendor (`res.partner`) form gets the same **Browse Supplier
Catalog** button when at least one Open punchout backend is
configured for it. This path always creates a *new* PO from the
returning cart.

## Open at supplier (per-product deep-link)

Configure a `product_url_template` on the vendor — a URL with a
`{vendor_code}` placeholder, e.g.
`https://supplier.example.com/parts/{vendor_code}`.

Then on any product that has a `seller_ids` line for that vendor:

- The product template form gets an **Open at supplier** button.
- Each row in the *Vendors* list gets an **Open at supplier** link
  per supplier — useful when a product has multiple vendors.

Both substitute the seller's `product_code` into the template and
open the result in a new tab.

## Auto-process on cart receipt

When the supplier returns a cart and the backend has a
`partner_id`, the session is auto-processed: the PO is created (or
appended to the pre-linked one) and the user lands on it directly.
Failures are reported in the chatter of both the session and the
pre-linked PO; the session stays in *To Process* so the purchaser
can retry by clicking *Process*.

## UoM mismatch warnings

If a returned cart line uses a UoM that differs from the product's
primary UoM, a chatter message lists the discrepancies on the PO so
the purchaser can verify before confirming. Same-category UoMs are
converted automatically by Odoo; cross-category or unmapped supplier
UoMs may have been silently coerced and warrant a manual check.

## Currency mismatch warning

If the cart's supplier prices are denominated in a currency
different from the resolved PO currency, a chatter message flags
the PO. Odoo stores the raw cart price as the line's `price_unit`
without conversion, so each line is a foreign-currency value
masquerading as the PO currency. Pick the right pricelist on the
vendor before kicking off the punchout, or convert the lines
manually before confirming.

## Tax handling

The cart's `price_unit` lands on the PO line tax-excluded by
convention — no Odoo-side conversion happens. Suppliers vary
(OCI's `NEW_ITEM-PRICE` and cXML's `UnitPrice/Money` are
tax-excluded for every supplier we've tested, but the protocols
don't *require* it). If your supplier sends tax-included prices,
configure their fiscal position so taxes are computed accordingly,
and validate against a known-good order before going live.

## Permissions

The Punchout smart button on the PO and the *Punchout Session*
column on order lines are visible only to users in
`base.group_system` (Administration / Settings). Regular purchasers
cannot read `punchout.session` records, so showing the controls
would just produce access errors.
