The goal of this module is to allow sending invoices in different format to external systems.

It extends the module `account_invoice_transmit_method`, adding options to configure an url and credentials (Basic Authentication).
In the UI a new button `Send ebill` send the invoice pdf to the configure url.

The actual sending of the invoice is manage by queue.job and the standard Odoo chatter on the invoice is used to inform the user on success/failure of the dispatch.
