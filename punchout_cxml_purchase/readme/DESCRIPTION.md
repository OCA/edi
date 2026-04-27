This is a glue module that enables purchase order creation from cXML shopping carts.

It is automatically installed when both `punchout_cxml` and `punchout_purchase` are installed.

Features:

- Parse cXML ItemIn elements from PunchOutOrderMessage responses
- Create purchase order lines with product, quantity, price
- Auto-create products from cart items (if enabled on backend)
- Map UoM using UNECE codes or backend-specific mappings
