Go to the form view of the suppliers and configure it with the following parameters:

* Individual/Company: *Company*
* the *TIN* (i.e. VAT number) is set (the VAT number is used by default when searching the supplier in the Odoo partner database)
* in the *Accounting* tab, create one or several *Invoice Import Configurations*.

This is the same as for the base account_invoice_import.

You can configure a mail gateway to import invoices from an email:

* Go to the menu *Settings > Technical > Email > Incoming Mail Servers* and setup the access (POP or IMAP) to the mailbox that will be used to receive the invoices,
* Unlike the configuration with base account_invoice_import, leave the "create a new record field" empty.
* From the account configuration menu, under journals, link the (purchase) journal to an alias, and in this way set the journal and company_id to use. This way using a catchall domain, you can link multiple email addresses to multiple journals in one or more companies.
