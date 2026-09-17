This is a glue module that enables purchase order creation from OCI shopping carts.

It is automatically installed when both `punchout_oci` and `punchout_purchase` are installed.

Features:

- Parse OCI NEW_ITEM form parameters from shopping cart responses
- Create purchase order lines with product, quantity, price, lead time
- Auto-create products from cart items (if enabled on backend)
- Map UoM using UNECE codes or backend-specific mappings
