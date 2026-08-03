This module has been started by lazy accounting users who hate entering
their vendor bills manually in Odoo. Almost all companies have several
vendor bills to enter regularly in the system from the same vendors:
phone bill, electricity bill, Internet access, train tickets, etc. Most
of these invoices are available as PDF. If we are able to automatically
extract from the PDF the required information to enter the invoice as
vendor bill in Odoo, then this module will create it automatically. To
know the full story behind the development of this module, read this
[blog
post](http://www.akretion.com/blog/akretions-christmas-present-for-the-odoo-community).

In order to reliably extract the required information from the invoice,
two international standards exist to describe an invoice in XML:

- [CII](http://tfig.unece.org/contents/cross-industry-invoice-cii.htm)
  (Cross-Industry Invoice) developed by
  [UN/CEFACT](http://www.unece.org/cefact) (United Nations Centre for
  Trade Facilitation and Electronic Business),
- [UBL](https://www.oasis-open.org/committees/ubl/) (Universal Business
  Language) which is an ISO standard ([ISO/IEC
  19845](https://www.iso.org/standard/66370.html))
  developed by [OASIS](https://www.oasis-open.org/) (Organization for
  the Advancement of Structured Information Standards).

Some e-invoice standards such as
[Factur-X](https://fnfe-mpe.org/factur-x/) propose to embed the XML
description of the invoice inside the PDF invoice. Other people think
that the future is pure-XML invoices: a European initiative called
[Peppol](https://peppol.org/) aims at setting up an open network to
exchange e-invoices as UBL XML. We don't know yet which standard and
which practice will prevail on electronic invoicing in the future, but
we hope that lazy accountants won't have to manually encode their vendor
bills in the near future. This module is here to help achieve this goal!

This module doesn't do anything useful by itself; it requires other
modules to work: each module adds a specific invoice format.

Here is how the module works:

- the user starts a wizard and uploads the PDF or XML invoice,
- if it is an XML file, Odoo will parse it to create the invoice
  (requires additional modules for specific XML formats, such as the
  module *account_invoice_import_ubl* for the UBL format),
- if it is a PDF file with an embedded XML file in Factur-X/CII format,
  Odoo will extract the embedded XML file and parse it to create the
  invoice (requires the module *account_invoice_import_facturx*),
- otherwise, Odoo will use the *invoice2data* Python library to try to
  interpret the text of the PDF (requires the module
  *account_invoice_import_invoice2data*),
- if the partner is matched, Odoo will use the partner's vendor bill
  import settings or reuse the accounting configuration from the latest
  posted invoice of that partner,
- otherwise, Odoo will create a new draft supplier invoice without a
  partner and propose to create or update the partner from the imported
  data.

This module also works with supplier refunds.
