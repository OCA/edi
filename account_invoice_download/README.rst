.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

========================
Account Invoice Download
========================

This module is the technical basis to automate the download of supplier invoices with Odoo. It must be used in combination with additionnal modules that add download backends. The technical name of these additionnal modules usually start with *account\_invoice\_download\_*.

Installation
============

Don't forget to choose and install additionnal *account\_invoice\_download\_** modules.

Configuration
=============

The configuration takes place in the menu *Accounting > Configuration > Import Vendor Bills > Download Bills*.

If you have several customer accounts with the same supplier, you need to create a *Download Bill Configuration* for each of them.

On each *Download Bill Configuration*, you will need to:

* select an Invoice Import Configuration,
* select a backend (the list of available backends will depend on the additionnal *account_invoice_download_** modules that you have installed),
* a download method: *Manual* or *Automatic*.

If you select *Automatic* as *download method*, you will have to enter the credentials of your account (login and password usually). If you select *Manual* as *download method* and you don't want to enter the credentials of your account, they will be prompted on each manual download run in Odoo. You can also choose to enter your login and not your password; in this case, only your password will be prompted on each manual download run.

If you have selected *Automatic* as *download method* on some accounts, make sure that the scheduled action *Vendor Bills Auto-Download* is active and has a daily frequency.

Usage
=====

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/226/10.0


Known issues / Roadmap
======================


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
