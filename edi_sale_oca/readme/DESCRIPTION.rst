Inbound
~~~~~~~
Receive sale orders from EDI channels.

Control sale order confirmation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can decide if the order should be confirmed by exchange type.

On your exchange type, go to advanced settings and add the following::

    [...]
    components:
        process:
            usage: input.process.sale.order
    [...]
    sale_order:
        default_confirm_order: true


TODO: shall we add an exchange type example as demo?
