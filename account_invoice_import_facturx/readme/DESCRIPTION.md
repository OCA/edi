**WARNING**: this module is now deprecated and has been marked as uninstallable. The parsing of Factur-X PDF invoices (and CII XML invoices) is now handled by the [factur-x](https://github.com/akretion/factur-x) python lib.

This module is an extension of the module *account_invoice_import*: it
adds the ability to import Factur-X 1.0 (i.e. ZUGFeRD 2.x) and ZUGFeRD
1.0 invoices. The [Factur-X](http://fnfe-mpe.org/factur-x/) standard is
based on
[CII](http://tfig.unece.org/contents/cross-industry-invoice-cii.htm)
(Cross-Industry Invoice) for electronic invoicing. A Factur-X invoice is
a PDF invoice with an embedded XML file in CII format that carries
structured information about the invoice.
