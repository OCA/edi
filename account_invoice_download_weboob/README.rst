.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===============================
Account Invoice Download Weboob
===============================

This module adds a weboob backend to the *account_invoice_download* module. `Weboob <http://weboob.org/>`_ (*Web Outside of Browsers*) is an opensource project that provides several applications to interact with websites without requiring to open them in a Web browser. It connects to websites via web-scrapping or APIs. Weboob provides `several APIs <http://dev.weboob.org/api/capabilities/index.html>`_ per topic: banking, job, cinema, weather, radio, etc. This Odoo module uses the *bill* API of Weboob to automatically download invoices from the websites of our suppliers and import them as vendors bills in Odoo. Weboob has a lot of `modules <http://weboob.org/modules>`_ (one per supported website), but only a small part of those modules provide the *bill* API. As of August 2018, Weboob has 26 modules that provide the *bill* API. Weboob welcomes the contribution of additionnal modules to support more websites. The weboob project was started by french developers, so the majority of modules to download invoices are for french suppliers (EDF, Orange, Bouygues Telecom, Free, etc.), but you are invited to develop and contribute new Weboob modules to add support for the main suppliers of your country. The `developer documentation <http://dev.weboob.org/>`_ of Weboob has a section named *Write a new module*!

Installation
============

Install the weboob library (TODO: check that it works with the stable version weboob 1.3 and not just the development version weboob 1.4):

.. code::

  sudo pip install weboob

Some Weboob modules require additionnal Python libraries. For example, the `Weboob module for Bouygues Telecom <http://weboob.org/modules#mod_bouygues>`_ requires:

.. code::

  sudo pip install python-jose

Weboob requires `MuPDF <https://mupdf.com/>`_. If you use Debian/Ubuntu, run:

.. code::

  sudo apt install mupdf-tools

Configuration
=============

First, install the Weboob modules that you plan to use:

* Go to the menu *Accounting > Configuration > Import Vendor Bills > Update Weboob Modules List*.
* Then, in the list of Weboob modules, click on each Weboob module that you plan to use and install it.

In the menu *Accounting > Configuration > Import Vendor Bills > Download Bills*, when you edit a *Download Bill Configuration*, you will now be able to select *Weboob* as *Backend*, and then you will see a new field *Weboob Module* that allows you to select the weboob module corresponding to the supplier.

Usage
=====

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/226/10.0

Known issues / Roadmap
======================

* Add support for Captcha solving (via CapCaptchaSolver ?)

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/edi/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Alexis de Lattre <alexis.delattre@akretion.com>

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
