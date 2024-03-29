==============
EDI Party data
==============

.. 
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! This file is generated by oca-gen-addon-readme !!
   !! changes will be overwritten.                   !!
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! source digest: sha256:6c2e2206f095872a298e2a1b29b5dc93ea5ab23deb640363c1fda7e4e207136e
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. |badge1| image:: https://img.shields.io/badge/maturity-Alpha-red.png
    :target: https://odoo-community.org/page/development-status
    :alt: Alpha
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fedi-lightgray.png?logo=github
    :target: https://github.com/OCA/edi/tree/14.0/edi_party_data_oca
    :alt: OCA/edi
.. |badge4| image:: https://img.shields.io/badge/weblate-Translate%20me-F47D42.png
    :target: https://translation.odoo-community.org/projects/edi-14-0/edi-14-0-edi_party_data_oca
    :alt: Translate me on Weblate
.. |badge5| image:: https://img.shields.io/badge/runboat-Try%20me-875A7B.png
    :target: https://runboat.odoo-community.org/builds?repo=OCA/edi&target_branch=14.0
    :alt: Try me on Runboat

|badge1| |badge2| |badge3| |badge4| |badge5|

Technical module for the EDI suite module to retrieve data for parties of an exchange.

This module provides default component
and a mixin to be used for registering new components for specific backends.

It's based on `partner_identification`
so that the party information will include allowed ID numbers for a given exchange.

You can configure which ID number categories are allowed on the exchange type.

.. IMPORTANT::
   This is an alpha version, the data model and design can change at any time without warning.
   Only for development or testing purpose, do not use in production.
   `More details on development status <https://odoo-community.org/page/development-status>`_

**Table of contents**

.. contents::
   :local:

Configuration
=============

ID numbers selection
~~~~~~~~~~~~~~~~~~~~

On the exchange type form, find the field "ID categories"
and set the categories allowed for that exchange type.

If not set, *all the IDs* of the partner will be exposed.

Name field
~~~~~~~~~~

On the exchange type form, modify the advanced settings
so that the work context of the component that is used (eg: generate)
contains `party_data_name_field`. For instance::

    components:
        generate:
            usage: my.generate
            work_ctx:
                party_data_name_field: name

Usage
=====

An handy util method is to retrive the component::

    from odoo.addons.edi_party_data_oca.utils import get_party_data_component

    component = get_party_data_component(exchange_record, partner)

    data = component.get_party()

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/edi/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us to smash it by providing a detailed and welcomed
`feedback <https://github.com/OCA/edi/issues/new?body=module:%20edi_party_data_oca%0Aversion:%2014.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Camptocamp

Contributors
~~~~~~~~~~~~

* Simone Orsi <simone.orsi@camptocamp.com>

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

.. |maintainer-simahawk| image:: https://github.com/simahawk.png?size=40px
    :target: https://github.com/simahawk
    :alt: simahawk

Current `maintainer <https://odoo-community.org/page/maintainer-role>`__:

|maintainer-simahawk| 

This module is part of the `OCA/edi <https://github.com/OCA/edi/tree/14.0/edi_party_data_oca>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
