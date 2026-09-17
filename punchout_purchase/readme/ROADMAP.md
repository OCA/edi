## Cart pre-fill — supplier never sees existing PO lines

The "Browse supplier catalog" button on a draft purchase order opens
the supplier's site, the user shops, and the returning cart's lines
are appended to the PO. **Existing lines on that PO are *not* sent to
the supplier** — the supplier always sees their own (initially empty)
cart on their site.

### Why it matters

A purchaser starts a draft PO, manually adds Product A (e.g. an
internal-catalog part with no supplier match). Then they click
"Browse supplier catalog", add Product B on the supplier's site,
and submit the cart. Result on the Odoo side:

```
PO has 2 lines: A (manual), B (from punchout)
```

The supplier only knows about B. When the user confirms the PO and
sends it (RFQ email, EDI), the supplier receives B. Product A is
on the Odoo PO but **isn't actually being procured from this
supplier** — and the user has no clear visual signal that the two
line origins differ.

### Mitigation today

- `purchase.order.line.punchout_session_id` records the session each
  line came from (or is empty for manual lines). Toggle the column
  visible via column-options on the PO line list.

### Real fix (deferred)

Both **OCI 5.0 extended modes** (`BACKGROUNDSEARCH`, `SOURCING`) and
**cXML** (`SetupRequest` with current cart payload) let the buyer send
the existing cart contents to the supplier as part of the punchout
setup, so the supplier can pre-fill their cart with what the buyer
already has. Implementing either:

- For OCI: probably a new method that builds an extended-mode setup
  payload including existing line refs (vendor codes only — supplier
  can't match arbitrary internal products).
- For cXML: extend the `PunchOutSetupRequest` template to include the
  current cart as `<ItemIn>` elements.

Both require coordination with the specific supplier's spec — TVH's
OCI 4.0 SELECT spec doesn't expose cart-pre-fill, and TVH's cXML
spec is request-only ("can be provided upon request" per their EMEA
doc page 10). Pick this up when those specs are in hand.

## "Browse from PO" wizard for multi-backend partners

`res.partner._find_punchout_backend()` picks the first open backend
for a partner. If a supplier exposes multiple backends (e.g. industrial
and agricultural catalogs at TVH/Bepco), the user gets an arbitrary
one. A simple wizard listing all open backends for the partner and
letting the user pick is the right follow-up.

**Status:** intentionally deferred. In the field a purchaser is
typically pinned to one catalog (either an industrial buyer *or*
an agricultural buyer at TVH, never both), so the multi-backend
case rarely materialises and the chooser-on-every-click would
just add a click for the common single-backend path. Revisit
when a real deployment needs it.

## "Open at supplier" multi-supplier wizard

`product.template.action_open_supplier_product` opens the first
matching supplierinfo's URL. Multi-supplier products would benefit
from a chooser ("which supplier did you want to look this up at?").
Same wizard pattern as the multi-backend case above.
