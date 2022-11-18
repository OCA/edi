Plug account_invoice_import into EDI machinery.


Control invoice confirmation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can decide if the invoice should be posted by exchange type.

On your exchange type, go to advanced settings and add the following::

    [...]
    components:
        process:
            usage: input.process.account.invoice
    [...]
    account_invoice:
        post_invoice: true
