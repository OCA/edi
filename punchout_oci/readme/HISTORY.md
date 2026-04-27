## 18.0.1.0.0 (2026)

- [MIG] Migration to Odoo 18.0. Original OCI protocol implementation by
  Hunki Enterprises BV (Holger Brunn).
- [IMP] Add OCI 4.0 to `oci_version` selection (label only, no
  4.0-specific functions yet — see ROADMAP).
- [FIX] HOOK_URL now carries a `punchout_session_token` query param
  (the session's buyer cookie) and the receive controller matches
  the returning cart on it. Previous behaviour matched "most recent
  draft session for backend", which mis-routed concurrent sessions.
- [IMP] Cart-payload size cap (configurable on backend) +
  `SELECT ... FOR UPDATE` lock on the matched session +
  `[punchout.oci.*]` log prefix for ops triage.
