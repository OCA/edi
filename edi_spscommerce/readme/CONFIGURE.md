## Dependencies

Odoo modules:

- ``edi_core_oca`` — exchange framework (backends, exchange types, records).
- ``edi_storage_oca`` — storage-backed transport (pulls ``fs_storage``).
- ``edi_exchange_template_oca`` — QWeb output templates.
- ``sale_stock``, ``account`` — sales/delivery orders and invoices.

Python packages:

- ``xmltodict`` — inbound parser (manifest ``external_dependencies``).
- ``fsspec`` + ``paramiko`` — for the SFTP transport (via ``fs_storage``;
  ``paramiko`` must be installed manually).

## Shipped configuration

- **Backend type** ``sps_rsx``.
- **Backend** ``SPS Commerce Backend`` with the SPS directory layout::

      input_dir_pending   = out        # SPS → you (live)
      input_dir_done      = archive    # you clean "out" yourself
      input_dir_error     = archive
      output_dir_pending  = in         # you → SPS (live)
      output_dir_done     = (empty)    # SPS deletes "in" files; unused
      output_dir_error    = (empty)

- **Exchange types** (all handler roles → ``edi.sps.handler``):

| Code | Direction | Document | Filename |
|------|-----------|----------|----------|
| ``sps_orders_in`` | input | ``rsx.document: orders`` | ``^PO`` |
| ``sps_order_acks_in`` | input | ``rsx.document: order_acks`` | ``^ACK`` (guess — confirm with SPS) |
| ``sps_shipments_out`` | output | ``rsx.document: shipments`` | ``SH-{dt}.xml`` |
| ``sps_invoices_out`` | output | ``rsx.document: invoices`` | ``IN-{dt}.xml`` |

- **Output templates** ``sps_shipments`` / ``sps_invoices``
  (``edi.exchange.template.output`` records + QWeb views, incl. shared
  fragments ``sps_meta``/``sps_address``/``sps_item_ids``), bound via
  ``output_template_id`` on the outbound types.
- **Exchange type rules**: *Send SPS ASN* button on done pickings,
  *Send SPS Invoice* button on posted customer invoices.

Exchange-type advanced settings (``rsx:`` block):

- ``document`` — expected RSX root (orders/shipments/invoices).
- ``sender_id`` / ``receiver_id`` — RSX Meta envelope ids.
- ``outbound_dir`` — local dir for the no-storage fallback.
- ``xsd_validate`` / ``xsd_path`` — optional XSD validation of inbound
  and outbound payloads (``lxml.etree.XMLSchema``). Enable
  ``xsd_validate`` and point ``xsd_path`` at a local copy of the SPS
  schema (e.g. ``Orders.xsd``); the schemas are user-supplied, not
  shipped.

## SPS SFTP map

SPS hosts the endpoint at ``sftp.spscommerce.com`` with fixed directory
pairs — ``out``/``testout`` inbound, ``in``/``testin`` outbound. Create
``archive`` on the SPS account first (rename fails otherwise); we must
clean ``out`` ourselves. SPS deletes ``in`` files during processing, so
outbound types have no ``check`` handler: ``output_sent`` is terminal
until an inbound ack (997/855) arrives.

## Partner and product matching

- **Partner**: ``res.partner.x_sps_trading_partner_id`` = the SPS
  trading-partner id (``OrderHeader.TradingPartnerId``, falling back to
  the Meta sender ids); ``res.partner.ref`` is matched and emitted as a
  fallback when the dedicated field is empty. The same id is what
  outbound templates emit in ``TradingPartnerId``.
- **Product**: ``OrderLine.VendorPartNumber``/``ApplicationId`` →
  ``default_code``; ``BuyerPartNumber`` → ``product.customer.code`` when
  installed; ``GTIN``/``EAN``/``ConsumerPackageCode`` → ``barcode``.
- **SPS references**: ``x_sps_location`` (first ``AddressLocationNumber``),
  ``x_sps_customer_ref`` (``OrderHeader.CustomerOrderNumber``) on the
  sale order; ``x_sps_line_ref`` (first line ``References.ReferenceID``)
  on order lines.
- **UOM**: RSX carries X12 355 codes in ``OrderQtyUOM``; the
  ``edi.sps.uom.map`` table (shipped with common codes) resolves them to
  ``uom.uom`` — unmapped codes or incompatible UoMs fall back to the
  product's UoM.
- **Payment terms**: RSX ``PaymentTerms.TermsNetDueDays`` resolves to
  ``account.payment.term`` via ``edi.sps.payment.term.map`` (no rows
  shipped — map your partners' net-day values). Unmapped orders fall
  back to the customer's default payment term.

## Customizing a partner

Each SPS relationship still has a mandatory-subset profile. Point the
partner's own exchange type at a copy of the shipped
``edi.exchange.template.output`` (or extend it via ``code_snippet``) —
no code changes needed.
