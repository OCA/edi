## 18.0.1.0.0 (2026)

- [MIG] Migration to Odoo 18.0.
- [IMP] `punchout.uom.mapping` now resolves supplier UoM codes through a
  6-tier chain: backend → supplier → global → UNECE → uom name → caller
  default.
- [IMP] Ship `data/uom_mapping_data.xml` with common non-UNECE codes as
  global defaults (STUECK, ST, STK, PC, PCS, EACH, KG, M, L).
- [IMP] Optional `supplier_id` scope on `punchout.uom.mapping`; both
  scopes (backend, supplier) are now optional.
- [FIX] `_get_browser_form_post_url` now produces RFC-clean URLs
  (no double slashes, no trailing slash before the query string).
- [IMP] Stored `name` field on `punchout.session` so Many2one displays
  show "Backend / 2026-04-26 14:02" instead of "punchout.session,42".
- [IMP] `punchout.backend` inherits `mail.thread` and tracks changes
  to state, protocol, URL, callback URL and session duration.
- [IMP] Smart button on the backend form opens the filtered list of
  sessions for that backend.
- [FIX] Session form's "Received" pane is hidden when
  `setup_request_response` is empty — only cXML actually fills it,
  so the pane was permanently blank for OCI/IDS sessions.
- [IMP] `session_retention_days` field on backend (default 90) +
  daily cron `_gc_punchout_sessions` that vacuums old sessions.
  Previous behaviour: the table grew without bound.
- [IMP] `max_response_size` field on backend (default 1 MiB) +
  `_check_response_size` helper used by the protocol controllers
  to reject oversized supplier payloads.
- [ADD] Dutch translation.

## 13.0.1.0.0 (2023-09-26)

- [ADD] First version.
