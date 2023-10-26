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
        env_ctx:
                # Values for the wizard
                default_confirm_order: true
                default_price_source: order
                # Custom keys, whatever you need
                random_one: true

Note that `env_ctx` will propagate all keys to the whole env so you can use it
for any kind of context related configuration. In the case of the sale order import wizard
here we are just passing defaults as we could do in odoo standard.

TODO: shall we add an exchange type example as demo?
