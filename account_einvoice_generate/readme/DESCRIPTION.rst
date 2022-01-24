This is a technical module that ensure compatibility between the e-invoice generation modules of the `OCA/edi project <https://github.com/OCA/edi/>`_. It doesn't bring any feature by itself. You must also install one of the 2 OCA modules that generate electronic invoices:

* **account_invoice_ubl**: add support for the UBL format (Universal Business Language),
* **account_invoice_facturx**: add support for the `Factur-X <http://fnfe-mpe.org/factur-x/factur-x_en/>`_ format.

See the README of each module for more information.

These 2 modules are able to embed an XML file in the PDF invoice and
this module ensure that these 2 modules are compatible.
