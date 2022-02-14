This module intends to create a base to be extended by local edi rules
for purchase.

In order to add a new integration, you need to create a listener:

.. code-block:: python

    class MyEventListener(Component):
        _name = "purchase.order.event.listener.demo"
        _inherit = "base.event.listener"
        _apply_on = ["purchase.order"]

        def on_button_confirm_purchase_order(self, move):
            """Add your code here"""
