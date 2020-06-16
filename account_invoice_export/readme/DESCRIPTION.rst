The goal of this module is to allow sending invoices in different format to external systems.

It is based on the module `account_invoice_transmit_method` and offer the option to configure `transmit.method` applied to customer with an url and credentials (Only Basic Authentication is implemented).

The function `_get_file_for_transmission_method` on `account.move` can be overriden to return the file description specific to a transmit method.

The actual sending of the invoice is manage by queue.job and the standard Odoo chatter on the invoice is used to inform the user on success/failure of the dispatch.
