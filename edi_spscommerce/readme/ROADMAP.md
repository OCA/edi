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
- ASN depth: ``OrderLevel`` → ``ItemLevel`` only for now — no
  ``PackLevel``/container hierarchy. SSC (SSCC) support stays on the
  roadmap for later, pending partner requirements.
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
- ~~ASN depth: ``PackLevel``/SSCC required, or ``OrderLevel→ItemLevel``
  enough?~~ — decided: ItemLevel for now (see Decisions).
- Invoice trigger: post of ``account.move``, or batch end-of-day?
- RSX filename convention: same ``PO``/``SH``/``IN`` prefixes + ``.xml``?

## Plan

- Iteration 1 (done): module scaffold, inbound codec, outbound QWeb
  templates + skeleton mappings, SFTP/manual transports, tests.
- Iteration 2: Orders full mapping (ship-to/GLN matching, payment terms,
  UOM table, currency, notes, dropship refs); split-per-document receive.
- Iteration 3: Shipments full mapping (carrier/SCAC, tracking, Dates,
  References); Invoices (terms, taxes, charges/allowances).
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
- [x] Split-per-document receive — batched ``<Orders>`` files spawn one
      child exchange record per extra ``<Order>`` (``parent_id`` link,
      single-order payload via ``rsx.serialize_orders``, picked up by the
      normal ``input_received`` → process pipeline)
- [x] Dropship flag — ``sale.order.x_sps_dropship`` from
      ``Meta.IsDropShip``; ship-to already resolves via ``Address[ST]``
- [x] ``x_sps_*`` fields — ``x_sps_location`` (first
      ``AddressLocationNumber``), ``x_sps_customer_ref``
      (``CustomerOrderNumber``) on sale orders, ``x_sps_line_ref`` (first
      line ``References.ReferenceID``) on order lines
- [x] Ship-to matching — ``Address[ST]`` creates/reuses a delivery child
      partner; ``res.partner.x_sps_location`` stores the GLN
      (``AddressLocationNumber``) and wins over street/city/zip matching
- [x] Order header tail — ``partner_shipping_id`` from
      ``Address[ST]`` (delivery child partner, matched on
      street/city/zip), ``currency_id`` from
      ``BuyersCurrency``/``SellersCurrency``, ``note`` from ``Notes``
- [ ] Orders → ``sale.order`` full mapping (order-level References
      beyond the line ref)
- [x] UOM map: X12 355 codes → ``uom.uom`` (``edi.sps.uom.map`` model +
      shipped data + lookup in the order import)
- [x] ``TsetPurposeCode`` handling — 00 original (create), 01
      cancellation (``action_cancel`` on the PO-matched order), 05
      replace (cancel + re-import), 06/07 confirmation/duplicate (no-op);
      Shipments outbound emits ``00``
- [x] Shipments header tail — ``TsetPurposeCode`` 00,
      ``ShipNoticeDate``/``ShipNoticeTime``, ``CarrierProNumber``
      (``carrier_tracking_ref``), ``SellersCurrency``,
      ``CarrierInformation``/``CarrierRouting`` (carrier name — SCAC
      needs a carrier-code map), ``ShipQtyUOM`` via reverse UOM map
- [ ] SSC/SSCC pack-level support — container hierarchy (``PackLevel``,
      SSCC codes) on top of the current ``OrderLevel`` → ``ItemLevel``
      ASN, once a partner requires it
- [x] Invoices header tail — ``PaymentTerms`` detail
      (``TermsNetDueDays``, term name, early-payment discount fields),
      header ``Taxes`` blocks from invoice tax lines, ``InvoiceQtyUOM``
      via ``_edi_sps_uom_code()``
- [x] Payment terms — ``edi.sps.payment.term.map`` maps RSX
      ``TermsNetDueDays`` → ``account.payment.term`` →
      ``sale.order.payment_term_id`` (empty map = partner default)
- [ ] Partner profile config — trading-partner id done
      (``res.partner.x_sps_trading_partner_id``, matched inbound and
      emitted outbound); remaining: per-partner code maps
      (carrier SCAC) and mandatory-field rules
- [x] ``rsx.xsd_validate`` + ``rsx.xsd_path`` — optional XSD validation
      of payloads via ``lxml.etree.XMLSchema`` (schemas user-supplied)
- [x] Inbound acks — ``sps_order_acks_in`` exchange type; OrderAck
      headers recorded on the matched sale order
      (``x_sps_ack_type``/``x_sps_ack_number``/``x_sps_ack_date``);
      unmatched acks logged and skipped
- [ ] Confirm with SPS: address types sent, purpose codes used,
      PackLevel/SSCC requirement, invoice trigger, RSX filename
      convention
- [ ] Verify against SPS ``testin``/``testout``
- [ ] Confirm SPS agreement permits OCA publication
- [ ] Regenerate ``README.rst``/``static/description`` with
      oca-gen-addon-readme before publishing
