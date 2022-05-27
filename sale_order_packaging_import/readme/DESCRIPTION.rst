This module extends the `sale_order_import` module to help on importing
the packaging information into the sales order line.

If for a sale line the product is detected by the code on one of its packaging,
then this corresponding packaging will be set on the order line.
Also the quantity received during the import will be set as the quantity of
packaging and not as the product quantity on the line.
