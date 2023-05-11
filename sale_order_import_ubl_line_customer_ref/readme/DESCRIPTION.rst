This is a glue module between `sale_order_import_ubl` and `sale_stock_line_customer_ref`.
It extracts customer references for specific lines from the XML received.

Since there's no specific element for customer reference in the UBL line,
the module will look into `cac:OrderLine/cac:Item/cbc:Note` for a string prefixed with `customer_ref:`.
