This module adds support for UBL, the `Universal Business Language (UBL) <http://ubl.xml.org/>`_ standard,
on purchase orders. The UBL 2.1 standard became the
`ISO/IEC 19845 <http://www.iso.org/iso/catalogue_detail.htm?csnumber=66370>`_ standard
in December 2015 (cf the `official announce <http://www.prweb.com/releases/2016/01/prweb13186919.htm>`_).

With this module, when you generate the purchase order or RFQ report:

* on a draft/RFQ/Bid Received purchase order, the PDF file will have an embedded XML *Request For Quotation* file compliant with the UBL 2.1 or 2.0 standard.

* on an approved purchase order, the PDF file will have an embedded XML *Order* file compliant with the UBL 2.1 or 2.0 standard.

If your supplier has Odoo and has installed the module *sale_order_import_ubl*, he will be able to import the PDF file and it will automatically create the quotation/sale order.
