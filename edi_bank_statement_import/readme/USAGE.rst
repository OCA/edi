For each bank/bank account, you need to create an exchange type.

On your exchange type, go to advanced settings and add the following::

    [...]
    components:
        process:
            usage: input.process.bank.statement


You can decide if the statements should be posted::

    [...]
    bank_statement:
        auto_post: true


You may also specify some context for the bank statement import wizard::

    [...]
    bank_statement:
        wiz_ctx:
            foo: "bar"
            default_sheet_mapping_id: 5
