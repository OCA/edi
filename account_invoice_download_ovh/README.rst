.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

====================
OVH Invoice Download
====================

This module adds an OVH backend to the *account_invoice_download* module. It allows you to auto-download `OVH <http://www.ovh.com>`_ invoices via the `OVH API <https://api.ovh.com/>`_.

Installation
============

Before installing the module, you need to install the `OVH python lib <https://github.com/ovh/python-ovh>`_ via the following command:

.. code::

  sudo pip install ovh

Configuration
=============

To configure this module, you need to go to the menu *Accounting > Configuration > Import Vendor Bills > Download Bills* and create one entry per OVH Account. Select *OVH* as *Backend*.

If you don't already have the required parameters to access the OVH API (Application key, Application secret and Consumer key) with the right access level on the APIs used by this module, use the wizard *Generate OVH API Credentials* that will be proposed once you have selected OVH as Backend.

Usage
=====

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
