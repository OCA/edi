This module intends to create a base to be extended by local edi rules
for stock.

In order to add a new integration for an stock picking, you need to create a listener:

.. code-block:: python

    class MyEventListener(Component):
        _name = "stock.picking.event.listener.demo"
        _inherit = "base.event.listener"
        _apply_on = ["stock.picking"]

        def on_validate(self, picking):
            """Add your code here about creation of record"""
