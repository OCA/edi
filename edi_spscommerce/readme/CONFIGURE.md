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

- **Backend type** ``sps``.
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
- ``xsd_validate`` — (planned) XSD validation toggle; schemas are
  user-supplied, not shipped.

## SPS SFTP map

SPS hosts the endpoint at ``sftp.spscommerce.com`` with fixed directory
pairs — ``out``/``testout`` inbound, ``in``/``testin`` outbound. Create
``archive`` on the SPS account first (rename fails otherwise); we must
clean ``out`` ourselves. SPS deletes ``in`` files during processing, so
outbound types have no ``check`` handler: ``output_sent`` is terminal
until an inbound ack (997/855) arrives.

## Test mode

The directory names carry the environment — same SFTP account, live
files in ``out``/``in``, test files in ``testout``/``testin``. All four
are configurable fields on the backend (``sps_*_dir_pending``, visible
on the Storage page for ``sps`` backends; the generic pending-dir
fields are hidden there since they're bypassed). Set **Test mode**
(``edi.backend.test_mode`` from ``edi_core_oca``):
``backend.get_conn_parameter()`` returns the live or test folder
accordingly — configured values are never rewritten.
``data/neutralize.sql`` in ``edi_core_oca`` sets test mode on all
backends for copied databases.

## Partner and product matching

- **Partner**: ``res.partner.ref`` = the SPS trading-partner id
  (``OrderHeader.TradingPartnerId``, falling back to the Meta sender
  ids). The id is also what outbound templates emit in
  ``TradingPartnerId``.
- **Product**: ``OrderLine.VendorPartNumber``/``ApplicationId`` →
  ``default_code``; ``BuyerPartNumber`` → ``product.customer.code`` when
  installed; ``GTIN``/``EAN``/``ConsumerPackageCode`` → ``barcode``.
- **UOM**: RSX carries X12 355 codes; a mapping table to ``uom.uom`` is
  planned — today quantities import in the product's UoM.

## Customizing a partner

Each SPS relationship still has a mandatory-subset profile. Point the
partner's own exchange type at a copy of the shipped
``edi.exchange.template.output`` (or extend it via ``code_snippet``) —
no code changes needed.
