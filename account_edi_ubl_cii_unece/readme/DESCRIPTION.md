This module extends the native module **account_edi_ubl_cii**: it adds few fields and constraints for UNECE codification.

This module adds two fields:

- a field **UNECE Payment Mean** on the Technical Payment Methods (model *account.payment.method*),
- a field **UNECE Type** on taxes (computed field that can be modified by the user).

It adds a constraint on taxes to raise an error in case of bad configurations. It hides the field **Tax Category Code** on non-VAT taxes.

