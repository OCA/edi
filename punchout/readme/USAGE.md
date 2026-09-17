To use this module:

1. Configure a punchout backend with your supplier's credentials
2. Set the backend state to "Open"
3. Click the **Access** button to start a punchout session
4. Browse the supplier's catalog and add items to your cart
5. Complete the checkout on the supplier's site - this sends the cart back to Odoo
6. The punchout session will show status "To Process" when the cart is received
7. Process the session to create purchase orders (requires `punchout_purchase` module)

**Session States:**

- **Draft**: Session created, waiting for supplier response
- **To Process**: Cart received from supplier, ready to create purchase order
- **Done**: Session processed successfully
- **Error**: Something went wrong (check error message)

**Auditing a backend:** the backend form carries a chatter and tracks
changes to `state`, `protocol`, `url`, `browser_form_post_url` and
`session_duration`. A "Sessions" smart button on the backend opens
the filtered list of every session that used it.

**See also:** when `punchout_purchase` is installed, additional entry
points appear (Browse Supplier Catalog from a draft PO and from a
vendor record, per-product "Open at supplier" deep-links). Refer to
that module's README for the purchase-side flows.
