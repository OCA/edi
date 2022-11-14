Plug account_statement_import into EDI machinery.


Control account statement import
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can decide if the order should be confirmed by exchange type.

On your exchange type, go to advanced settings and add the following::

    [...]
    components:
        process:
            usage: input.process.account.bank.statement

TODO: shall we add an exchange type example as demo?
