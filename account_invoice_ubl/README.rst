.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===================
Account Invoice UBL
===================

This module adds support for UBL, the `Universal Business Language (UBL)
<http://ubl.xml.org/>`_ standard, on invoices. The UBL 2.1 standard became the
`ISO/IEC 19845 <http://www.iso.org/iso/catalogue_detail.htm?csnumber=66370>`_
standard in December 2015 (cf the `official announce
<http://www.prweb.com/releases/2016/01/prweb13186919.htm>`_).

With this module, you can generate customer invoices/refunds:

* in PDF format with an embedded UBL XML file
* as an XML file with an optional embedded PDF file

This module supports UBL version 2.1 (used by default) and 2.0.

Configuration
=============

In the menu *Invoicing > Configuration > Settings > Invoicing*, under
*Electronic Invoices*, check the value of 2 options:

* *XML Format embedded in PDF invoice* : if you want to have an UBL XML file
   embedded inside the PDF invoice, set it to
   *Universal Business Language (UBL)*
* if you work directly with XML invoices and you want to have the PDF invoice
  in base64 inside the XML file, enable the *Embed PDF in UBL XML Invoice*.

Usage
=====

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/226/11.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/edi/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Alexis de Lattre <alexis.delattre@akretion.com>
* Andrea Stirpe <a.stirpe@onestein.nl>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
