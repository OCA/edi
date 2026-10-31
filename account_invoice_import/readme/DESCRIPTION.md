This module has been started by lazy accounting users who hate enter
they vendor bills manually in Odoo. Almost all companies have several
vendor bills to enter regularly in the system from the same vendors:
phone bill, electricity bill, Internet access, train tickets, etc. Most
of these invoices are available as PDF. If we are able to automatically
extract from the PDF the required information to enter the invoice as
vendor bill in Odoo, then this module will create it automatically. To
know the full story behind the development of this module, read this
[blog
post](http://www.akretion.com/blog/akretions-christmas-present-for-the-odoo-community).

In order to reliably extract the required information from the invoice,
two international standards exists to describe an Invoice in XML:

- [CII](http://tfig.unece.org/contents/cross-industry-invoice-cii.htm)
  (Cross-Industry Invoice) developped by
  [UN/CEFACT](http://www.unece.org/cefact) (United Nations Centre for
  Trade Facilitation and Electronic Business),
- [UBL](http://ubl.xml.org/) (Universal Business Language) which is an
  ISO standard ([ISO/IEC
  19845](http://www.iso.org/iso/catalogue_detail.htm?csnumber=66370))
  developped by [OASIS](https://www.oasis-open.org/) (Organization for
  the Advancement of Structured Information Standards).

The [Factur-X](http://fnfe-mpe.org/factur-x/) invoice standard embeds a CII XML
file inside the PDF invoice: this is the concept of hybrid invoice.

This module has native support for UBL XML, CII XML and Factur-X. You can install additional modules (for example account_invoice_import_simple_pdf) to support other invoice formats.

Here is how the module works:

- the user starts a wizard and uploads the PDF or XML invoice,
- if it is an XML file, Odoo will parse it to create the invoice
- if it is a PDF file with an embedded XML file in Factur-X/CII format,
  Odoo will extract the embedded XML file and parse it to create the
  invoice,
- if there is already a draft supplier invoice for this supplier with
  the same invoice number, Odoo will display a warning,
- otherwise, Odoo will create a new draft vendor bill and
  attach the PDF or XML invoice file to it.

This module also works with vendor refunds.
