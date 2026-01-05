During UBL/CII invoice import, Odoo attempts to retrieve or create a partner bank
account based on the bank details provided in the electronic document.

When a partner bank account already exists in the system but is **archived**,
the standard import logic doesn't find it. As a result, Odoo attempts to create
a new bank account record with the same bank account number.

This leads to a failure due to the SQL uniqueness constraint on partner bank
accounts, as duplicated bank account numbers are not allowed, even when one of
them is archived.
