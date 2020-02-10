To configure this module, you need to:

* go to the menu *Sales > Configuration > Products > Units of Measures* and check the *UNECE Code* for the units of measures.
* go to the menu *Invoicing > Configuration > Accounting > Taxes* and, for each tax, set a *UNECE Type Code* and a *UNECE Category Code*.
* go to the menu *Invoicing > Configuration > Management > Payment Methods* and assign a *UNECE Code* to the payment methods that are selected in the payment modes.

To avoid the manual configuration of taxes, look for a module *l10n_XX_account_tax_unece* in the OCA project of your localization; if such a module exists (it exists at least for the Netherlands and France), install it and it will auto-configure the taxes created by your localization.
