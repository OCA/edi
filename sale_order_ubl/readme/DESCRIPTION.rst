This module adds support for UBL, the `Universal Business Language (UBL) <http://ubl.xml.org/>`_ standard,
on sale orders. The UBL 2.1 standard became the
`ISO/IEC 19845 <http://www.iso.org/iso/catalogue_detail.htm?csnumber=66370>`_ standard
in December 2015 (cf the `official announce <http://www.prweb.com/releases/2016/01/prweb13186919.htm>`_).

With this module, when you generate the sale order report:

* on a draft/sent quotation, the PDF file will have an embedded XML *Quotation* file compliant with the UBL 2.1 or 2.0 standard.

* on a confirmed sale order, the PDF file will have an embedded XML *Order Response Simple* file compliant with the UBL 2.1 or 2.0 standard.
