## 18.0.1.0.0 (2026)

- [MIG] Migration to Odoo 18.0. Original IDS protocol implementation by
  Hunki Enterprises BV (Holger Brunn).
- [FIX] hook_url now carries a `punchout_session_token` query param
  (the session's buyer cookie) and the receive controller matches
  the returning cart on it. Previous behaviour matched "most recent
  draft session for backend", which mis-routed concurrent sessions.
- [IMP] Cart-payload size cap (configurable on backend) +
  `SELECT ... FOR UPDATE` lock on the matched session +
  `[punchout.ids.*]` log prefix for ops triage.
