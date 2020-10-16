This module defines a Base for Electronic Documents and it's flow.
Three models are created:

* Electronic Document Format: Defines a way to integrate
* Electronic Document: Each received or sent document
* Electronic Document mixin: Models used to generate documents

This module does not any change by itself, it should be used with other modules
that defines the specific integration.

It is base on Odoo `account_edi` module, but it tries to be more generic.
