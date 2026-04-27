## 18.0.1.0.0 (2026)

- [ADD] First version: cXML cart → purchase order glue.
- [IMP] UoM lookup routed through
  `punchout.uom.mapping._get_uom_by_supplier_code` (full 6-tier
  resolution).
- [FIX] Drop `detailed_type` from auto-created products
  (Odoo 18 removed the field).
- [FIX] Use `supplier_code` (not the non-existent `external_code`) when
  scanning backend UoM mappings.
- [FIX] Auto-created products now carry the supplier-provided UoM, so
  the resulting order line doesn't trip the same-category constraint.
- [IMP] Warn (logger) when a supplier-part code matches multiple
  products for the same partner. Picks the first deterministically
  rather than silently.
