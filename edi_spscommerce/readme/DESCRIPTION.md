EDI integration with **SPS Commerce** via their canonical **RSX XML**
format (namespace ``http://www.spscommerce.com/RSX``, schema v7.7.0), on
top of the **OCA EDI framework** (``edi_core_oca``), targeting Odoo 19.0.

RSX is SPS's proprietary normalized schema: one document type covers
every trading partner — SPS maps each partner's native X12/EDIFACT/API
behind it, so we integrate once instead of per-partner segment maps.

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
  — inbound files polled from ``out``/``testout``, outbound uploaded to
  ``in``/``testin``;
- **Manual drop (fallback)** — import wizard for inbound, local
  directory for outbound.

This module is a POC in active development: the mappings cover the core
fields and defer the long schema tail (carrier detail, pack levels,
charges/allowances, taxes detail) to the partner implementation guide.

*Not affiliated with or endorsed by SPS Commerce.*
