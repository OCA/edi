This module is a small module above the *base_ubl* module;
it adds the generation of the *PaymentMeans* UBL block.
I decided to make it a separate module because it depends
on the module *account_payment_unece* which itself depend on
*account_banking_payment_export*, and I didn't want to add
these dependencies on the *base_ubl* module.
