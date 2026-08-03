Go to the form view of the suppliers and configure them with the following
parameters:

- Individual/Company: *Company*
- the *VAT Number* (this field is used by default when searching the
  supplier in the Odoo partner database)
- in the *Accounting* tab, configure the *Vendor Bills Import* fields:
  default product, default expense account, default taxes, forced invoice
  line description, single-line import, and forced purchase journal.

You can configure a mail gateway to import invoices from an email:

- Go to the menu *Settings \> Technical \> Email \> Incoming Mail
  Servers* and setup the access (POP or IMAP) to the mailbox that will
  be used to receive the invoices,
- In the section *Actions to perform on incoming mails*, set the field
  *Create a new record* to *Wizard to import supplier invoices/refunds*
  (model *account.invoice.import*).
- Go to the menu *Invoicing \> Configuration \> Settings*: in the
  section *Vendor Bills Import*, configure the adjustment accounts used
  for rounding differences. You can also enable supplier bank account
  auto-creation.
- If you are in a multi-company setup, enter the email of the mailbox
  used to import invoices in the field *Mail Gateway: Destination
  E-mail*; it will be used to import the invoice in the proper company.
