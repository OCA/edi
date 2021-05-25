This module has been started by lazy accounting users who hate enter they vendor bills manually in Odoo. Almost all companies have several vendor bills to enter regularly in the system from the same vendors: phone bill, electricity bill, Internet access, train tickets, etc. Most of these invoices are available as PDF. If we are able to automatically extract from the PDF the required information to enter the invoice as vendor bill in Odoo, then this module will create it automatically. To know the full story behind the development of this module, read this `blog post <http://www.akretion.com/blog/akretions-christmas-present-for-the-odoo-community>`_.

In order to reliably extract the required information from the invoice, two international standards exists to describe an Invoice in XML:

* `CII <http://tfig.unece.org/contents/cross-industry-invoice-cii.htm>`_ (Cross-Industry Invoice) developped by `UN/CEFACT <http://www.unece.org/cefact>`_ (United Nations Centre for Trade Facilitation and Electronic Business),
* `UBL <http://ubl.xml.org/>`_ (Universal Business Language) which is an ISO standard (`ISO/IEC 19845 <http://www.iso.org/iso/catalogue_detail.htm?csnumber=66370>`_) developped by `OASIS <https://www.oasis-open.org/>`_ (Organization for the Advancement of Structured Information Standards).

Some e-invoice standards such as `Factur-X <http://fnfe-mpe.org/factur-x/>`_ propose to embed the XML description of the invoice inside the PDF invoice. Other people think that the futur is pure-XML invoices: a European initiative called `PEPPOL <https://peppol.eu/>`_ aims at setting up an open network to exchange e-invoices as UBL XML. We don't know yet which standard and which practice will prevail on electronic invoicing in the future, but we hope that lazy accountants won't have to manually encode their vendor bills in the near future. This module is here to help achieve this goal!

This module doesn't do anything useful by itself ; it requires other modules to work: each modules adds a specific invoice format.

Here is how the module works:

* the user starts a wizard and uploads the PDF or XML invoice,
* if it is an XML file, Odoo will parse it to create the invoice (requires additional modules for specific XML formats, such as the module *account_invoice_import_ubl* for the UBL format),
* if it is a PDF file with an embedded XML file in Factur-X/CII format, Odoo will extract the embedded XML file and parse it to create the invoice (requires the module *account_invoice_import_facturx*),
* otherwise, Odoo will use the *invoice2data* Python library to try to interpret the text of the PDF (requires the module *account_invoice_import_invoice2data*),
* if there is already some draft supplier invoice for this supplier, Odoo will propose to select one to update or create a new draft invoice,
* otherwise, Odoo will directly create a new draft supplier invoice and attach the PDF to it.

This module also works with supplier refunds.
