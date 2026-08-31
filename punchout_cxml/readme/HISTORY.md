## 18.0.1.0.0 (2026)

- [MIG] Migration to Odoo 18.0. Original cXML protocol implementation by
  ACSONE SA/NV (Thomas Binsfeld, Benjamin Willig).
- [FIX] Drop the session form view inheritance that renamed the
  generic "Setup" / "Response" notebook tabs to "cXML Setup" /
  "cXML Response". The override applied unconditionally, so OCI and
  IDS sessions also showed cXML labels when this module was installed
  alongside others.
- [IMP] Cart-payload size cap (configurable on backend) +
  `SELECT ... FOR UPDATE` lock on the matched session +
  `[punchout.cxml.*]` log prefix for ops triage.
- [ADD] **Test Connection** button on the backend form: sends a real
  `PunchOutSetupRequest` and verifies the supplier responds with a
  valid setup response. Catches wrong URL / wrong credentials /
  expired DTD link before the user sees a confusing redirect failure
  mid-flow.
