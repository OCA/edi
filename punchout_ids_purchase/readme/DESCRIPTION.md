This is a glue module that enables purchase order creation from IDS shopping carts.

It is automatically installed when both `punchout_ids` and `punchout_purchase` are installed.

Features:

- Parse IDS XML OrderItem elements from shopping cart responses
- Create purchase order lines with product, quantity, price
- Support for delivery date/week from IDS OrderInfo
- Auto-create products from cart items with VAT mapping
- Handle price basis for quantity-based pricing
