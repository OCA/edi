This module has been started by lazy accounting users who hate enter they supplier invoices manually in Odoo. Almost all companies have several supplier invoices to enter regularly in the system from the same suppliers: phone bill, electricity bill, Internet access, train tickets, etc. Most of these invoices are available as PDF. We dream that we would be able to automatically extract from the PDF the required information to enter the invoice as supplier invoice in Odoo. To know the full story behind the development of this module, read this `blog post <http://www.akretion.com/blog/akretions-christmas-present-for-the-odoo-community>`_.

In the future, we believe we will have structured information embedded inside the metadata of PDF invoices. There are 2 main standards for electronic invoicing:

* `CII <http://tfig.unece.org/contents/cross-industry-invoice-cii.htm>`_ (Cross-Industry Invoice) developped by `UN/CEFACT <http://www.unece.org/cefact>`_ (United Nations Centre for Trade Facilitation and Electronic Business),
* `UBL <http://ubl.xml.org/>`_ (Universal Business Language) which is an ISO standard (`ISO/IEC 19845 <http://www.iso.org/iso/catalogue_detail.htm?csnumber=66370>`_) developped by `OASIS <https://www.oasis-open.org/>`_ (Organization for the Advancement of Structured Information Standards).

For example, there is already a standard in Germany called `ZUGFeRD <http://www.pdflib.com/knowledge-base/pdfa/zugferd-invoices/>`_ which is based on CII.

This module doesn't do anything useful by itself ; it requires other modules to work: each modules adds a specific invoice format.

Here is how the module works:

* the user starts a wizard and uploads the PDF or XML invoice,
* if it is an XML file, Odoo will parse it to create the invoice (requires additional modules for specific XML formats, such as the module *account_invoice_import_ubl* for the UBL format),
* if it is a PDF file with an embedded XML file in ZUGFeRD/CII format, Odoo will extract the embedded XML file and parse it to create the invoice (requires the module *account_invoice_import_zugferd*),
* otherwise, Odoo will use the *invoice2data* Python library to try to interpret the text of the PDF (requires the module *account_invoice_import_invoice2data*),
* if there is already some draft supplier invoice for this supplier, Odoo will propose to select one to update or create a new draft invoice,
* otherwise, Odoo will directly create a new draft supplier invoice and attach the PDF to it.

This module also works with supplier refunds.
