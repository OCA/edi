The current implementation supports the OCI **SELECT** function (browse a
supplier's catalog, return a cart, parse `NEW_ITEM-*` fields). The
`oci_version` field accepts 3.0 / 4.0 / 5.0 and is passed to the
supplier as `OCI_VERSION` in the redirect URL, but the following OCI
4.0 / 5.0 functions are not yet implemented and need supplier-specific
work to land — every supplier diverges from the spec in subtle ways:

- **VALIDATE** (4.0+) — server-side price / availability check before
  PO placement. Needs the supplier's auth profile (commonly URL
  parameter signing, sometimes HMAC, occasionally encrypted
  USERNAME/PASSWORD on 5.0). Best added as a focused follow-up module
  (e.g. `punchout_oci_validate`) so it can be reviewed against real
  supplier docs.
- **DETAIL** (4.0+) — buyer requests an item-detail screen rendered by
  the supplier (`~OkCode=DETAIL` + `NEW_ITEM-VENDORMAT`). The
  protocol-aware version of the per-product "Open at supplier"
  deep-link in `punchout_purchase` (which today just constructs a
  URL from a template — no protocol involved). Add when a target
  supplier confirms DETAIL support; TVH's EMEA spec does not list it.
- **SOURCING** (4.0+) — supplier proposes alternative items.
- **Multi-window punchout** (4.0+) — open a new browser window per
  supplier session.
- **Image rendering** (5.0+) — `NEW_ITEM-IMAGE_URL[n]` and friends; the
  parser ignores them today.
- **OCI 5.0 transport security** — mandatory TLS is observed (Odoo's
  HTTP layer already enforces it server-side); HMAC-signed parameters
  and encrypted credential fields are supplier-specific.
