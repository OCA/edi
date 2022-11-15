Plug account_statement_import into EDI machinery.


Configure exchange type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On your exchange type, go to advanced settings and add the following::

    [...]
    components:
        process:
            usage: input.process.account.bank.statement
