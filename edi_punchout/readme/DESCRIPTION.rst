This module implements several punchout protocols:

- IDS (very DE specific)
- OCI (quite EU specific)

Allowing users to transfer orders from a webshop supporting the one of the above to Odoo and the other way around.

Note that the current implementation doesn't protect the login credentials of the webshop because of the way the protocols work, so you should enable this functionality only for trusted users.

The above could be helped by implementing cXML or the secure OCI extension, which is not currently the case.
