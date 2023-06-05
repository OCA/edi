
EDI Exchange Type "Advanced Settings"

.. code-block:: yaml

   components:
      process:
         usage: input.process.sale.order

   sale_order_import:
      price_source: order
      confirm_order: false
      wiz_ctx:
         file_ext: 'edi'
         release: 'd96a'
         doc_type: 'rfq'


- price_source. Can be 'order' or 'pricelist'
- confirm_order. False by default
- wiz_ctx. Wizard's context
  - file_ext. File extensions supported. By default: 'txt,d96a'
  - release. EDIFACT format release.
  - doc_type. ('rfq', "Request for Quotation") | ('order', "Order"). Default 'order'

This module struggles with EDIFACT format, if you need X12 format you will need something like sale_order_import_x12 module.

Regardless format, a concret document should need a concret specification nammed release. For example Amazon uses "D96A" specification.

See <https://www.stedi.com/edi/edifact>
