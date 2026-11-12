EDI integration with **SPS Commerce** via their canonical **RSX XML**
format (namespace ``http://www.spscommerce.com/RSX``, schema v7.7.0), on
top of the **OCA EDI framework** (``edi_core_oca``), targeting Odoo 19.0.

RSX is SPS's proprietary normalized schema: one document type covers
every trading partner — SPS maps each partner's native X12/EDIFACT/API
behind it, so we integrate once instead of per-partner segment maps.

X12 vs RSX: trading partners traditionally exchange **ANSI X12** files —
flat text built from positional segments (``ISA``/``GS``/``ST``/``PO1``)
and fixed-length elements. SPS translates each partner's X12 into RSX
before delivery, so the wire format this module parses and emits is
**always RSX XML** — raw X12 never reaches Odoo. (X12 *code lists* do
appear inside RSX as values, e.g. the 355 unit-of-measure and BIG
invoice-type codes.)

Documents covered:

- **Orders inbound** — RSX ``Orders`` → draft ``sale.order``
- **Shipments outbound (ASN)** — ``stock.picking`` → RSX ``Shipments``
- **Invoices outbound** — ``account.move`` → RSX ``Invoices``

All three share one group vocabulary (Address, Dates, References, Notes,
PaymentTerms, Taxes, ChargesAllowances, CarrierInformation, part-number
id block). Inbound payloads are parsed by ``services/rsx.py``
(``xmltodict``) into schema-shaped dicts; outbound payloads are rendered
by QWeb ``edi.exchange.template.output`` templates that consume the
business records directly.

Transport is pluggable per exchange record:

- **SPS-hosted SFTP** (``sftp.spscommerce.com``) via ``edi_storage_oca``
  — inbound files polled from ``out``, outbound uploaded to ``in``
  (directory names configurable on the backend);
- **Manual drop (fallback)** — import wizard for inbound, local
  directory for outbound.

This module is a POC in active development: the mappings cover the core
fields and defer the long schema tail (carrier detail, pack levels,
charges/allowances, taxes detail) to the partner implementation guide.

*Not affiliated with or endorsed by SPS Commerce.*

**Legal notice:** RSX schemas, documentation, trading-partner
implementation guides, and the SPS Commerce name and logos are the
proprietary property of SPS Commerce, Inc. This module contains no SPS
Commerce schemas or specifications — users must obtain the applicable
RSX documentation and any required licenses directly from SPS Commerce.
Use of this module to exchange documents with SPS Commerce is subject to
your agreement with SPS Commerce.
