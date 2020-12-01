This module intends to create a base to be extended by local edi rules
for accounting.

In order to add a new integration for an account, you need to create a listener:

.. code-block:: python

    class MyEventListener(Component):
        _name = "account.move.event.listener.demo"
        _inherit = "base.event.listener"
        _apply_on = ["account.move"]

        def on_post_account_move(self, move):
            """Add your code here about creation of record"""

A skip if decorator can be added in order to make some checks on the state of the move
