OVH Supplier Invoice
====================

This module allows you to download the `OVH <http://www.ovh.com>` invoices via the `SoAPI <http://www.ovh.com/soapi/>` of OVH. When you start the wizard, it will get the invoices from OVH and create supplier invoices in Odoo with the PDF of the invoice as attachment.

This module support multiple OVH accounts.

Installation
============

Before installing the module, you need to install the `SOAPpy python lib <https://pypi.python.org/pypi/SOAPpy>` via the following command:

sudo pip install SOAPpy

Configuration
=============

To configure this module, you need to go to the menu *Accounting > Configuration > Miscellaneous > OVH Accounts* and create one entry per OVH Account. You are not obliged to enter the OVH password for each accounts ; you can enter the password at runtime.

For each account, you have the choice between 2 methods:

* *Without Product* (the default method): the invoice lines created will not have a product and you must configure an expense account and an optional analytic account that will be used for all the OVH invoice lines.

* *With Product*: this method is more complex because you have to create OVH products in Odoo for each product or each family of product that you have on your OVH invoices. These products must have an *Internal Reference* 'OVH-prefix' where *prefix* is the first caracters of the domain field of OVH invoice lines. If you don't know the domain of your OVH invoice lines, you can start the wizard to get OVH invoices and you will get an error message on each domain that didn't find a match in Odoo product database. If you also want to set the analytic account, you can use the Odoo module *product_analytic_account* that allows you to configure analytic accounts on the product or on the product category, or use the official module *account_analytic_default*.

You also need to have a partner OVH as supplier with the VAT number *FR22424761419*.

Usage
=====

To start the wizard to download the OVH invoices, go to the menu *Accounting > Periodic Processing > Recurring Entries > Get OVH Invoices*. In the wizard options, you can delete the OVH accounts that you don't want to use and you must enter the passwords corresponding to the accounts if you didn't set the password in the accounts configuration. You can also set a *From Date* to exclude the OVH invoices older than this date.

Then click on the *Get Invoices* button and wait a few seconds. When the OVH invoices are created as supplier invoices in Odoo, it will display the list view of the supplier invoices created. If some OVH invoices are already present in the list of OVH supplier invoices in Odoo, they will be skipped.

Credits
=======

Contributors
------------

* Alexis de Lattre <alexis.delattre@akretion.com>
