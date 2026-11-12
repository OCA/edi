## Inbound Orders — manual drop (no storage)

1. Open **EDI → Exchanges → Import SPS RSX**.
2. Pick the exchange type, upload the RSX ``Orders`` file.
3. The wizard creates an ``edi.exchange.record`` in ``input_pending``
   and runs receive → validate → process immediately.

Expected result: one draft ``sale.order`` per ``<Order>`` —
``PurchaseOrderNumber`` → ``client_order_ref``, ``Dates[002]`` →
``commitment_date``, one line per ``LineItem``. The exchange record is
linked as the order's EDI origin. ``TsetPurposeCode`` other than ``00``
(original) raises — cancel/change documents are handled manually for
now.

## Inbound Orders — via SPS SFTP

1. SPS drops a ``PO*`` file into ``out``/``testout``.
2. The storage poller creates an ``input_pending`` record; the input
   sync cron receives, validates, and processes it; processed files move
   to ``archive``.

## Outbound Shipments (ASN)

- **Manual**: open a done delivery order → **Send SPS ASN**.
- **Automatic**: ``stock.picking.button_validate`` queues a Shipments
  exchange for done pickings when the partner is enabled on the type.
- **Retrigger**: call ``picking._edi_sps_queue_shipments(force=True)``
  (server action / shell) — skips pickings with an existing record
  unless ``force``.

The picking is rendered by the ``sps_shipments`` template and uploaded
to ``output_dir_pending`` (SPS: ``in``/``testin``) as ``SH-<dt>.xml``,
or written to ``rsx.outbound_dir`` without storage.

## Outbound Invoices

Open a posted customer invoice (or credit note) → **Send SPS Invoice**.
The move is rendered by ``sps_invoices`` (``DI`` for invoices, ``CR``
for credit notes) and delivered the same way.

## Extension points

- ``services/rsx.py`` — inbound codec: ``parse``/``parse_orders`` +
  ``FORCE_LIST`` for repeatable groups.
- ``edi.exchange.template.output`` — outbound documents; copy a shipped
  template per partner profile, or use ``code_snippet`` for extra render
  values.
- ``edi.sps.handler`` — handler roles; partner/product matching in
  ``_find_partner``/``_find_product``.
- ``edi.exchange.type.advanced_settings_edit`` — ``rsx.*`` config.
