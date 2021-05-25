Go to the form view of the suppliers and configure it with the following parameters:

* Individual/Company: *Company*
* the *TIN* (i.e. VAT number) is set (the VAT number is used by default when searching the supplier in the Odoo partner database)
* in the *Accounting* tab, create one or several *Invoice Import Configurations*.

You can configure a mail gateway to import invoices from an email:

* Go to the menu *Settings > Technical > Email > Incoming Mail Servers* and setup the access (POP or IMAP) to the mailbox that will be used to receive the invoices,
* In the section *Actions to perform on incoming mails*, set the field *Create a new record* to *Wizard to import supplier invoices/refunds* (model *account.invoice.import*).
* If you are in a multi-company setup, you also have to go to the menu *Invoicing > Configuration > Settings*: in the section *Invoice Import*, enter the email of the mailbox used to import invoices in the field *Mail Gateway: Destination E-mail* (it will be used to import the invoice in the proper company).
