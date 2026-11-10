**Status:** in progress

## Decisions

- SPS **RSX XML** (schema v7.7.0) is the payload format — normalized
  across partners by SPS; proprietary to SPS but standard connector
  practice (cf. ``account_avatax``, ``delivery_sendcloud``).
  - Rejected: extending the raw-X12 codec in ``edi_x12_poc`` — per-partner
    segment maps duplicate work SPS already did.
  - Rejected: ``base_business_document_import``/UBL — the wire format is
    fixed by SPS.
- Module name ``edi_spscommerce``.
  - Rejected: ``edi_rsx`` — RSX is SPS's proprietary namespace; a generic
    name would overstate portability.
- Transport: **SPS-hosted SFTP** (``sftp.spscommerce.com``) via
  ``edi_storage_oca`` — ``out``/``testout`` in, ``in``/``testin`` out,
  ``archive`` for processed; no outbound ``check`` (SPS deletes ``in``
  files, ``output_sent`` terminal until an inbound ack).
  - Rejected: SPS REST API/AS2 — would need ``edi_webservice_oca`` and
    loses the file-based audit trail.
- Inbound codec ``services/rsx.py`` via ``xmltodict`` — schema-shaped
  dicts (RSX element names verbatim), ``FORCE_LIST`` for ``[0..*]``
  groups; the handler does RSX→Odoo translation.
- Outbound generation via **QWeb** ``edi.exchange.template.output`` —
  templates consume ``record`` directly (mapping lives in data;
  per-partner overrides need no code). Handler injects only ``meta``.
  - *2026-11 — supersedes programmatic ``etree`` builders.*
  - *2026-11 — record-direct templates supersede ``_edi_sps_*_values``
    dict builders — one mapping surface.*
- **Batching**: ``<Order>/<Shipment>/<Invoice>[1..*]`` — plan to split
  one file into one exchange record per document (error isolation).
  - Rejected: one record per file — a bad document would block the batch.
- Inbound Orders create **draft** ``sale.order``; ``TsetPurposeCode``
  drives create/cancel/change (only ``00`` implemented).
- XSD validation behind ``rsx.xsd_validate`` for the test phase;
  schemas are user-supplied, not shipped.
- OCA publication: license **LGPL-3**; no vendored SPS materials (tests
  use hand-written fixtures); nominative use of the name; confirm the
  SPS agreement doesn't mark RSX confidential before publishing.

## Open questions

- Which address types does the partner send (``ST``+``BY`` only, or
  separate ``BT``)? Drives partner-matching fallback order.
- Do we get ``TsetPurposeCode`` 01/04/05 (cancel/change) or originals only?
- ASN depth: ``PackLevel``/SSCC required, or ``OrderLevel→ItemLevel`` enough?
- Invoice trigger: post of ``account.move``, or batch end-of-day?
- RSX filename convention: same ``PO``/``SH``/``IN`` prefixes + ``.xml``?

## Plan

- Iteration 1 (done): module scaffold, inbound codec, outbound QWeb
  templates + skeleton mappings, SFTP/manual transports, tests.
- Iteration 2: Orders full mapping (ship-to/GLN matching, payment terms,
  UOM table, currency, notes, dropship refs); split-per-document receive.
- Iteration 3: Shipments full mapping (carrier/SCAC, tracking,
  PackLevel/SSCC); Invoices (terms, taxes, charges/allowances).
- Iteration 4: partner profile config; verify vs SPS ``testin``/``testout``.
- Iteration 5: inbound acks (997/855), cancel/change order handling.

## Tasks

- [x] Scaffold ``edi_spscommerce`` (manifest, handler, backend type, three
      exchange types, access rules, import wizard, tests)
- [x] Codec ``services/rsx.py`` — xmltodict parse (verified against the
      real ``Orders.xml`` sample)
- [x] Outbound generation via ``edi_exchange_template_oca`` — QWeb views
      consuming ``record`` + template records on the outbound types
      (skeleton mappings)
- [x] Split design doc into ``readme/`` fragments (this doc)
- [ ] Split-per-document receive (one exchange record per ``<Order>``)
- [ ] ``x_sps_*`` fields — ``x_sps_location`` (partner GLN/location id),
      ``x_sps_customer_ref`` / ``x_sps_line_ref`` on sale orders
- [ ] Orders → ``sale.order`` full mapping (ship-to match/create, UOM
      table, payment terms, currency, notes, dropship refs)
- [ ] UOM map: X12 355 codes → ``uom.uom`` (module data + lookup)
- [ ] ``TsetPurposeCode`` 01/04/05 — cancel/change order handling
- [ ] Shipments full mapping (carrier/SCAC, tracking, PackLevel/SSCC,
      Dates, References)
- [ ] Invoices full mapping (payment terms, taxes, charges/allowances,
      BOL/PRO)
- [ ] Partner profile config (trading-partner id, code maps,
      per-partner mandatory fields)
- [ ] Implement ``rsx.xsd_validate`` (user-supplied schema path)
- [ ] Inbound acks — 997/855 exchange types
- [ ] Confirm with SPS: address types sent, purpose codes used,
      PackLevel/SSCC requirement, invoice trigger, RSX filename
      convention
- [ ] Verify against SPS ``testin``/``testout``
- [ ] Confirm SPS agreement permits OCA publication
- [ ] Regenerate ``README.rst``/``static/description`` with
      oca-gen-addon-readme before publishing
