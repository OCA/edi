.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

================================
Account Invoice Import Directory
================================

This module extends the functionality of account_invoice_import and allows to
run the import of invoices through an automatic process scanning some
directories on the Odoo server.

Installation
============

To install this module, you need to:

#. Just install it.

Configuration
=============

This module is complementary with account_invoice_import, so please report to
its configuration requisites to be sure to well use it.
Then go to Accounting and create an Invoice Import directory Configuration.
This configuration will require:

* a name
* a directory path on your Odoo server where the system will scan for file to upload
* an after import strategy: you can either decide to move the file to an archive directory or either delete it

This module also require to set a technical user on the company. (Go to
company Form and configure it on the Configuration tab).
This is useful in a multi-company context to prevent to use Admin user to
create invoices.

NB: Be sure that the system user running the odoo main process has enough
rights to read in all directories used in configurations.

Usage
=====

A cron is available to be scheduled to scan each configuration directories
and will launch a queue job per file found.


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/226/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/edi/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://odoo-community.org/logo.png>`_.

Contributors
------------

* Cédric Pigeon <cedric.pigeon@acsone.eu>

Do not contact contributors directly about support or help with technical issues.

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
