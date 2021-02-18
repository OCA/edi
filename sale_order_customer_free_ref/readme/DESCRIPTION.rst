The goal of this module is to improve on the `client_order_ref` on `sale.order`.

By default, Odoo only has one field to handle the customer reference of a sales order.

However, an order provided by the buyer can contain an id (PO number) and a free reference.
When exchanging with the other parties, you sometimes need to differentiate them.
For instance, this is required by some EDI flows.

To help with this, this module adds two specific fields for them and transforms the
`client_order_ref` standard field into a computed one.

The two new fields are also passed on to generated invoices.
