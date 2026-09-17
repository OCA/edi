After installing this module with demo data:

1. Go to *PunchOut → PunchOut Backends*
2. Open *Demo OCI Mock Supplier (in-Odoo, end-to-end)*
3. Click *Access* in the form header
4. The mock catalog page opens. Set a quantity on one or more rows.
5. Click *Submit cart →*. The browser auto-POSTs back to Odoo's OCI
   receive controller, the response is parsed, and a draft purchase
   order is created on the session.

The mock products span several UoM types (EA, PCE, M, L, KG, plus an
unmapped code) so the run exercises every tier of the
`punchout.uom.mapping` resolution chain.
