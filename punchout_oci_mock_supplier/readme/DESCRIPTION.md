Self-contained OCI supplier mock for end-to-end testing of the punchout
modules.

The module registers two HTTP routes on the same Odoo instance:

- `GET  /punchout_oci_mock_supplier/catalog`  — renders a fake catalog
- `POST /punchout_oci_mock_supplier/checkout` — returns an interstitial
  form that auto-POSTs OCI fields (`NEW_ITEM-DESCRIPTION[1]`, etc.)
  back to the buyer's `HOOK_URL`

The routes live under the module's own namespace so they can't clash
with any current or future `/punchout/...` controller.

Together with the demo backend included with the module, this gives a
runboat user a complete one-click OCI roundtrip: open the backend list,
click *Access* on the demo record, set quantities on a couple of
products, click *Submit cart*, and a draft purchase order shows up on
the originating session.

The mock refuses to POST to any HOOK_URL outside the current Odoo
instance — public runboats never relay OCI carts to arbitrary URLs.

Not for production use.
