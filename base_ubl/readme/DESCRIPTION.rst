This is the base module for the implementation of the `Universal Business
Language (UBL) <http://ubl.xml.org/>`_ standard.  The UBL standard became the
`ISO/IEC 19845 <http://www.iso.org/iso/catalogue_detail.htm?csnumber=66370>`_
standard in January 2016 (cf the `official announce
<http://www.prweb.com/releases/2016/01/prweb13186919.htm>`_).

This module contains methods to generate and parse UBL files. This module
doesn't do anything useful by itself, but it is used by several other modules:

* *purchase_order_ubl* that generate UBL purchase orders,
* *sale_order_import_ubl* that imports UBL sale orders.
* *account_invoice_import_ubl* that imports UBL invoices,
