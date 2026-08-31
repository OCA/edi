## 18.0.1.0.0 (2026)

- [ADD] First version: IDS cart → purchase order glue.
- [IMP] UoM lookup routed through
  `punchout.uom.mapping._get_uom_by_supplier_code` (full 6-tier
  resolution).
- [FIX] Drop `detailed_type` from auto-created products
  (Odoo 18 removed the field).
- [FIX] Use `supplier_code` (not the non-existent `external_code`) when
  scanning backend UoM mappings.
- [FIX] Tighten product matching domain — the previous fallback
  (`OR barcode = False`) matched almost any product in the database
  and grafted unrelated sellers onto them.
- [IMP] Warn (logger) when an ArtNo matches multiple products for
  the same partner. Picks the first deterministically rather than
  silently.
- [ADD] `_post_create_product_hook(product, raw_data)` — empty
  extension point fired once per newly-created product. Lets private
  / glue modules enrich the product (image, dimensions, HS code,
  brand) from the supplier's REST API without monkey-patching.
  ``raw_data`` is the parsed IDS OrderItem lxml objectify element.
